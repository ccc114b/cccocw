use ndarray::{Array, ArrayD, IxDyn};

struct Tensor {
    data: ArrayD<f64>,
    grad: Option<ArrayD<f64>>,
    children: Vec<ChildInfo>,
    id: usize,
}

#[derive(Clone)]
struct ChildInfo {
    id: usize,
    local_grad: ArrayD<f64>,
}

struct TensorPool {
    tensors: Vec<Tensor>,
    counter: usize,
}

impl TensorPool {
    fn new() -> Self {
        Self { tensors: Vec::new(), counter: 0 }
    }
    
    fn alloc(&mut self, data: ArrayD<f64>, children: Vec<ChildInfo>) -> usize {
        let id = self.counter;
        self.counter += 1;
        self.tensors.push(Tensor { data, grad: None, children, id });
        id
    }
    
    fn get(&self, id: usize) -> &Tensor { &self.tensors[id] }
    fn len(&self) -> usize { self.tensors.len() }
    
    fn get_grad(&self, id: usize) -> Option<&ArrayD<f64>> {
        self.tensors[id].grad.as_ref()
    }
    
    fn set_grad(&mut self, id: usize, grad: ArrayD<f64>) {
        self.tensors[id].grad = Some(grad);
    }
    
    fn take_grad(&mut self, id: usize) -> Option<ArrayD<f64>> {
        self.tensors[id].grad.take()
    }
}

fn scalar(data: f64) -> ArrayD<f64> {
    Array::from_elem(IxDyn(&[]), data)
}

fn add(a_id: usize, b_id: usize, pool: &mut TensorPool) -> usize {
    let a = pool.get(a_id).data.clone();
    let b = pool.get(b_id).data.clone();
    let data = &a + &b;
    let children = vec![
        ChildInfo { id: b_id, local_grad: scalar(1.0) },
        ChildInfo { id: a_id, local_grad: scalar(1.0) },
    ];
    pool.alloc(data, children)
}

fn mul(a_id: usize, b_id: usize, pool: &mut TensorPool) -> usize {
    let a = pool.get(a_id).data.clone();
    let b = pool.get(b_id).data.clone();
    let data = &a * &b;
    let children = vec![
        ChildInfo { id: a_id, local_grad: b.clone() },
        ChildInfo { id: b_id, local_grad: a.clone() },
    ];
    pool.alloc(data, children)
}

fn relu(x_id: usize, pool: &mut TensorPool) -> usize {
    let x = pool.get(x_id).data.clone();
    let data = x.mapv(|v| v.max(0.0));
    let mask = x.mapv(|v| if v > 0.0 { 1.0 } else { 0.0 });
    let children = vec![ChildInfo { id: x_id, local_grad: mask }];
    pool.alloc(data, children)
}

fn log(x_id: usize, pool: &mut TensorPool) -> usize {
    let x = pool.get(x_id).data.clone();
    let data = x.mapv(|v| v.ln());
    let inv_x = x.mapv(|v| 1.0 / v);
    let children = vec![ChildInfo { id: x_id, local_grad: inv_x }];
    pool.alloc(data, children)
}

fn exp(x_id: usize, pool: &mut TensorPool) -> usize {
    let x = pool.get(x_id).data.clone();
    let exp_data = x.mapv(|v| v.exp());
    let children = vec![ChildInfo { id: x_id, local_grad: exp_data.clone() }];
    pool.alloc(exp_data, children)
}

fn pow(x_id: usize, exp: f64, pool: &mut TensorPool) -> usize {
    let x = pool.get(x_id).data.clone();
    let data = x.mapv(|v| v.powf(exp));
    let grad = x.mapv(|v| exp * v.powf(exp - 1.0));
    let children = vec![ChildInfo { id: x_id, local_grad: grad }];
    pool.alloc(data, children)
}

fn backward(root_id: usize, pool: &mut TensorPool) {
    let n = pool.len();
    let mut visited = vec![false; n];
    let mut topo: Vec<usize> = Vec::new();
    
    fn build_topo(pool: &TensorPool, v: usize, visited: &mut Vec<bool>, topo: &mut Vec<usize>) {
        if visited[v] { return; }
        visited[v] = true;
        for child in &pool.get(v).children {
            build_topo(pool, child.id, visited, topo);
        }
        topo.push(v);
    }
    
    build_topo(pool, root_id, &mut visited, &mut topo);
    pool.set_grad(root_id, scalar(1.0));
    
    for &v in topo.iter().rev() {
        let grad = pool.get_grad(v).unwrap().clone();
        let children: Vec<ChildInfo> = pool.get(v).children.clone();
        
        for child in children {
            let child_grad = &child.local_grad * &grad;
            let existing = pool.take_grad(child.id);
            let new_grad = match existing {
                Some(e) => &e + &child_grad,
                None => child_grad,
            };
            pool.set_grad(child.id, new_grad);
        }
    }
}

fn main() {
    println!("=== Test 1: f(a,b) = (a+b)^2 ===");
    let mut pool = TensorPool::new();
    let a_id = pool.alloc(scalar(3.0), vec![]);
    let b_id = pool.alloc(scalar(4.0), vec![]);
    let c_id = add(a_id, b_id, &mut pool);
    let d_id = mul(c_id, c_id, &mut pool);
    
    backward(d_id, &mut pool);
    
    println!("a = 3, b = 4");
    println!("c = a + b = {}", pool.get(c_id).data);
    println!("d = c^2 = {}", pool.get(d_id).data);
    println!("dd/da = {} (expected: 14)", pool.get(a_id).grad.as_ref().unwrap());
    println!("dd/db = {} (expected: 14)", pool.get(b_id).grad.as_ref().unwrap());
    
    println!("\n=== Test 2: relu with negative input ===");
    let mut pool2 = TensorPool::new();
    let x_id = pool2.alloc(scalar(-2.0), vec![]);
    let y_id = relu(x_id, &mut pool2);
    backward(y_id, &mut pool2);
    println!("relu(-2) = {} (expected: 0)", pool2.get(y_id).data);
    println!("drelu/dx = {} (expected: 0)", pool2.get(x_id).grad.as_ref().unwrap());
    
    println!("\n=== Test 3: relu with positive input ===");
    let mut pool3 = TensorPool::new();
    let x_id = pool3.alloc(scalar(3.0), vec![]);
    let y_id = relu(x_id, &mut pool3);
    backward(y_id, &mut pool3);
    println!("relu(3) = {} (expected: 3)", pool3.get(y_id).data);
    println!("drelu/dx = {} (expected: 1)", pool3.get(x_id).grad.as_ref().unwrap());
    
    println!("\n=== Test 4: log ===");
    let mut pool4 = TensorPool::new();
    let x_id = pool4.alloc(scalar(2.0), vec![]);
    let y_id = log(x_id, &mut pool4);
    backward(y_id, &mut pool4);
    println!("log(2) = {} (expected: ~0.693)", pool4.get(y_id).data);
    println!("dlog/dx = {} (expected: 0.5)", pool4.get(x_id).grad.as_ref().unwrap());
    
    println!("\n=== Test 5: exp ===");
    let mut pool5 = TensorPool::new();
    let x_id = pool5.alloc(scalar(2.0), vec![]);
    let y_id = exp(x_id, &mut pool5);
    backward(y_id, &mut pool5);
    println!("exp(2) = {} (expected: ~7.389)", pool5.get(y_id).data);
    println!("dexp/dx = {} (expected: ~7.389)", pool5.get(x_id).grad.as_ref().unwrap());
    
    println!("\n=== Test 6: x^3 ===");
    let mut pool6 = TensorPool::new();
    let x_id = pool6.alloc(scalar(2.0), vec![]);
    let y_id = pow(x_id, 3.0, &mut pool6);
    backward(y_id, &mut pool6);
    println!("2^3 = {} (expected: 8)", pool6.get(y_id).data);
    println!("d(x^3)/dx = {} (expected: 12)", pool6.get(x_id).grad.as_ref().unwrap());
}