import numpy as np

K = np.array([[1.0, 0.0], [0.0, 1.0]])
V = np.array([[2.0, 0.0], [0.0, 3.0]])

def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

def compute_attention(q, k, v, mask=None):
    d_k = q.shape[-1]

    scores = (q @ K.T)/np.sqrt(d_k)

    if mask is not None:
        scores = np.where(mask, -np.inf, scores)

    weights = softmax(scores)

    output = weights @ v
    return weights, output

conditions = [
    ("Q1=",np.array([1.0, 0.0]), None), 
    ("Q2=",np.array([0.0, 1.0]), None),
    ("Q3=",np.array([1.0, 0.0]), np.array([False, True]))
]

for title, q, mask in conditions:
    weights, output = compute_attention(q, K, V, mask)
    print(title)
    print(q)
    print(f"weights = {np.round(weights, 4)},{np.round(weights, 3)}")
    print(f"sum = {np.sum(weights)}")
    print(f"output = {np.round(output, 4)},{np.round(output, 4)}")