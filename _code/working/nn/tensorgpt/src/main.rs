mod gpt;
mod nn;
mod tensor;

use gpt::{inference, train, GPT};
use tensor::TensorPool;

fn main() {
    println!("=== TensorGPT Demo ===\n");

    println!("Loading data from input.txt...");
    let data = std::fs::read_to_string("input.txt").expect("Failed to read input.txt");
    let docs: Vec<String> = data
        .lines()
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .collect();
    println!("Loaded {} documents", docs.len());

    let mut all_chars: Vec<char> = docs.iter().flat_map(|s| s.chars()).collect();
    all_chars.sort();
    all_chars.dedup();
    let uchars: Vec<char> = all_chars.clone();
    let vocab_size = uchars.len() + 1;
    let BOS = uchars.len();
    println!("Vocab size: {} (including BOS)", vocab_size);

    let n_embd = 16;
    let n_layer = 1;
    let n_head = 4;
    let block_size = 16;

    println!(
        "\nCreating GPT model (n_embd={}, n_layer={}, n_head={}, block_size={})...",
        n_embd, n_layer, n_head, block_size
    );

    let mut pool = TensorPool::new();
    let model = GPT::new(vocab_size, n_embd, n_layer, n_head, block_size, &mut pool);
    let params = model.params();
    println!("Model has {} parameters", params.len());

    let mut optimizer = tensor::Adam::new(params, 0.01, 0.9, 0.99, 1e-8);

    let num_steps = 50;
    println!("\nTraining for {} steps...", num_steps);
    train(
        &model,
        &mut optimizer,
        &docs,
        &uchars,
        BOS,
        &mut pool,
        num_steps,
    );

    println!("\nGenerating samples...");
    inference(&model, &uchars, BOS, &mut pool, 5, 0.5);
}
