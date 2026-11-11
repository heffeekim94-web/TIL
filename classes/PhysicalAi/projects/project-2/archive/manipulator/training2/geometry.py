"""충돌 판정용 기하: URDF 에서 팔 몸체 표면 점 · 몸체(base) 부품 상자를 만들고, GPU 에서 점 ↔ 상자 부호 있는 거리를 잰다.

USD 로 바꾸면 고정 관절로 붙은 링크가 한 몸체로 합쳐져 (적재함 · 프로파일 기둥 · 받침 · 차체 = base_footprint 하나)
PhysX 접촉 센서로는 어느 부품에 닿았는지 모른다 → URDF 의 링크 단위 모양으로 직접 잰다. 음수 = 겹침.
"""
import struct
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

URDF = Path(__file__).resolve().parents[1] / 'robot_usd' / 'urdf' / 'robot.urdf'
MOVING = ('revolute', 'continuous', 'prismatic')


def rpy_T(xyz, rpy):
    r, p, y = rpy
    cx, sx, cy, sy, cz, sz = np.cos(r), np.sin(r), np.cos(p), np.sin(p), np.cos(y), np.sin(y)
    T = np.eye(4)
    T[:3, :3] = [[cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx],
                 [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx],
                 [-sy, cy * sx, cy * cx]]
    T[:3, 3] = xyz
    return T


def origin(el):
    o = el.find('origin') if el is not None else None
    if o is None:
        return np.eye(4)
    return rpy_T([float(v) for v in o.get('xyz', '0 0 0').split()], [float(v) for v in o.get('rpy', '0 0 0').split()])


def load_mesh(path):
    """삼각형 (F, 3, 3). obj · stl(이진/문자)."""
    if path.lower().endswith('.obj'):
        V, F = [], []
        for ln in open(path, errors='ignore'):
            if ln.startswith('v '):
                V.append([float(x) for x in ln.split()[1:4]])
            elif ln.startswith('f '):
                idx = [int(t.split('/')[0]) for t in ln.split()[1:]]
                idx = [i - 1 if i > 0 else len(V) + i for i in idx]
                F += [(idx[0], idx[k], idx[k + 1]) for k in range(1, len(idx) - 1)]
        return np.array(V)[np.array(F, dtype=int)] if F else np.zeros((0, 3, 3))
    data = open(path, 'rb').read()
    if data[:5] == b'solid' and b'facet' in data[:400]:
        v = [list(map(float, l.split()[1:4])) for l in data.decode(errors='ignore').splitlines() if l.strip().startswith('vertex')]
        return np.array(v).reshape(-1, 3, 3)
    n = struct.unpack('<I', data[80:84])[0]
    arr = np.frombuffer(data[84:84 + n * 50], dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
    return arr['v'].reshape(-1, 3, 3).astype(float)


class Urdf:
    def __init__(self, path=URDF):
        root = ET.parse(path).getroot()
        self.links = {l.get('name'): l for l in root.findall('link')}
        self.parent_joint = {j.find('child').get('link'): j for j in root.findall('joint')}

    def body_of(self, link):
        """고정 관절을 따라 올라가 USD 에서 합쳐질 몸체와 링크 → 몸체 변환 (관절 0 일 때)."""
        T = np.eye(4)
        while link in self.parent_joint and self.parent_joint[link].get('type') not in MOVING:
            j = self.parent_joint[link]
            T = origin(j) @ T
            link = j.find('parent').get('link')
        return link, T

    def links_in_body(self, body):
        return [(n, T) for n in self.links for b, T in [self.body_of(n)] if b == body]

    def tris(self, link, kind='visual'):
        out = []
        for el in self.links[link].findall(kind):
            g = el.find('geometry')
            m = g.find('mesh') if g is not None else None
            if m is None:
                continue
            t = load_mesh(m.get('filename')) * np.array([float(s) for s in m.get('scale', '1 1 1').split()])
            To = origin(el)
            out.append(t @ To[:3, :3].T + To[:3, 3])
        return np.concatenate(out) if out else np.zeros((0, 3, 3))

    def boxes(self, link):
        """충돌 상자 [(중심 T 4x4 링크 기준, 반 크기 3)] — box 는 그대로, 메시는 링크 기준 축정렬 상자."""
        out = []
        for el in self.links[link].findall('collision'):
            g = el.find('geometry')
            if g is None:
                continue
            To = origin(el)
            if g.find('box') is not None:
                out.append((To, np.array([float(v) for v in g.find('box').get('size').split()]) / 2))
            elif g.find('mesh') is not None:
                m = g.find('mesh')
                v = load_mesh(m.get('filename')).reshape(-1, 3) * np.array([float(s) for s in m.get('scale', '1 1 1').split()])
                if len(v):
                    v = v @ To[:3, :3].T + To[:3, 3]
                    c = np.eye(4); c[:3, 3] = (v.min(0) + v.max(0)) / 2
                    out.append((c, (v.max(0) - v.min(0)) / 2))
        return out


def sample_surface(tris, spacing, seed=0):
    rng = np.random.default_rng(seed)
    a = 0.5 * np.linalg.norm(np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]), axis=1)
    n = int(a.sum() / spacing ** 2) + 1
    k = rng.choice(len(tris), n, p=a / a.sum())
    u, v = rng.random(n), rng.random(n)
    f = u + v > 1
    u[f], v[f] = 1 - u[f], 1 - v[f]
    t = tris[k]
    return t[:, 0] + u[:, None] * (t[:, 1] - t[:, 0]) + v[:, None] * (t[:, 2] - t[:, 0])


def box_surface(half, spacing):
    """상자 표면 점 (중심 원점)."""
    pts = []
    for ax in range(3):
        for s in (-1, 1):
            o = [i for i in range(3) if i != ax]
            g = [np.linspace(-half[i], half[i], max(2, int(2 * half[i] / spacing) + 1)) for i in o]
            A, B = np.meshgrid(*g, indexing='ij')
            p = np.zeros((A.size, 3)); p[:, o[0]] = A.ravel(); p[:, o[1]] = B.ravel(); p[:, ax] = s * half[ax]
            pts.append(p)
    return np.unique(np.concatenate(pts).round(6), axis=0)


@dataclass
class BaseBox:
    name: str          # URDF 링크 이름 (또는 cup_<칸>_<번호>)
    tag: str           # profile · chassis · stand · rack · cup · arm_base
    T: np.ndarray      # base_footprint 기준 4x4
    half: np.ndarray


def base_boxes(u: Urdf, base_body='base_footprint'):
    """base 몸체에 합쳐진 부품 상자. 바퀴 · 조향은 따로 움직이는 몸체라 뺌 (팔이 닿을 수 없는 높이)."""
    out = []
    for link, T_lb in u.links_in_body(base_body):
        if link.startswith(('profile_link', 'profile_fixing', 'profile_camera')):
            tag = 'profile'
        elif link.startswith('gripper_park'):
            tag = 'stand'
        elif link.startswith('rack'):
            tag = 'rack'
        elif link == 'link1':
            tag = 'arm_base'
        else:
            tag = 'chassis'
        for T, h in u.boxes(link):
            out.append(BaseBox(link, tag, T_lb @ T, h))
    return out


def obb_sdf_min(P, C, R, H, chunk=8):
    """점들 P (N, M, 3) 와 상자 K 개 (중심 C (N, K, 3), 회전 R (N, K, 3, 3), 반 크기 H (N|1, K, 3)) 의
    점별 최소가 아닌 상자별 최소 부호 있는 거리 (N, K) [m]."""
    out = []
    H = H.expand(C.shape[0], -1, -1)
    for k0 in range(0, C.shape[1], chunk):
        c, r, h = C[:, k0:k0 + chunk], R[:, k0:k0 + chunk], H[:, k0:k0 + chunk]
        L = torch.einsum('nmd,nkde->nmke', P, r) - torch.einsum('nkd,nkde->nke', c, r)[:, None]   # (N, M, k, 3) 상자 좌표
        d = L.abs() - h[:, None]
        sd = d.clamp(min=0).norm(dim=-1) + d.max(dim=-1).values.clamp(max=0)
        out.append(sd.min(dim=1).values)
    return torch.cat(out, 1)
