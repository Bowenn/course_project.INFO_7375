import argparse
import json
import os
import math

import tiktoken
import torch
from omegaconf import OmegaConf
from tqdm import trange
from lm.model import DecoderLM
from lm.utils import determine_device, enable_tf32
from lm.train import compute_language_modeling_loss


def softmax_with_temperature(
    logits: torch.FloatTensor, temperature: float
) -> torch.FloatTensor:
    """Turns logits into probabilities under softmax (with temperature)

    Args:
        logits: a 2d torch tensor of token ids (B x V)
        temperature: temperature of the softmax function

    Returns:
        a 2d torch tensor of token probabilities (B x V)
    """

    # to avoid division by 0
    temperature = max(temperature, 1e-5)
    logits_t = logits / temperature
    return torch.softmax(logits_t, dim=-1)


@torch.inference_mode()
def generate(
    model: DecoderLM,
    device: str,
    tokenizer: tiktoken.Encoding,
    prefixes: list[str],
    batch_size: int,
    max_new_tokens: int = 32,
    temperature: float = 0.1,
) -> list[str]:
    """Generates completions conditioned on prefixes; computes perplexity

    Args:
        model: the language model
        device: device to put the tensors on
        tokenizer: the tokenizer
        prefixes: a list of strings as prefixes for generation
        batch_size: number of prefixes to batch together during generation
        max_new_tokens: the number of tokens to generate for each prefix
        temperature: temperature parameter of softmax

    Returns:
        a list of strings (continuations to prefixes)

    Note: you should implement a batched version of this function by
        left-padding tokenized prefixes with `tokenizer.eot_token` so that all
        sequences have equal length. `attention_mask` should be set to 0.0 for
        padding tokens, and 1.0 everywhere else.
    """

    generations = []
    total_loss, total_count = 0.0, 0

    for i in trange(0, len(prefixes), batch_size):
        # tokenize and left-pad the batch with the end-of-text token
        batch = [tokenizer.encode(p) for p in prefixes[i : i + batch_size]]
        max_len = max(len(ids) for ids in batch)
        input_ids = torch.tensor(
            [[tokenizer.eot_token] * (max_len - len(ids)) + ids for ids in batch],
            dtype=torch.long, device=device,
        )
        attention_mask = torch.tensor(
            [[0.0] * (max_len - len(ids)) + [1.0] * len(ids) for ids in batch],
            device=device,
        )

        new_tokens = []
        for _ in range(max_new_tokens):
            # the model only accepts n_positions tokens, so keep the most recent ones
            ctx_ids = input_ids[:, -model.n_positions:]
            ctx_mask = attention_mask[:, -model.n_positions:]
            logits = model(ctx_ids, attention_mask=ctx_mask)[:, -1, :]   # (B, V)
            probs = softmax_with_temperature(logits, temperature)
            next_token = torch.multinomial(probs, num_samples=1)        # (B, 1)

            new_tokens.append(next_token)
            input_ids = torch.cat([input_ids, next_token], dim=1)
            attention_mask = torch.cat(
                [attention_mask, torch.ones_like(next_token, dtype=attention_mask.dtype)], dim=1
            )

        gen_ids = torch.cat(new_tokens, dim=1)                          # (B, max_new_tokens)
        generations.extend(tokenizer.decode(row.tolist()) for row in gen_ids)

        # perplexity of the generated text under the model
        loss = compute_language_modeling_loss(gen_ids, model(gen_ids))
        total_loss += loss.item() * gen_ids.shape[0]
        total_count += gen_ids.shape[0]

    perplexity = math.exp(total_loss / total_count)

    print(f"Perplexity: {perplexity}")
    return generations


def main():
    enable_tf32()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=OmegaConf.load,
        required=True,
        help="the yaml config file used for model training",
    )
    parser.add_argument(
        "--prefixes",
        type=str,
        required=True,
        help="a json file with a list of strings as prefixes for generation",
    )
    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=32,
        help="number of new tokens to generate",
    )
    parser.add_argument(
        "--temperature", type=float, default=0.1, help="temperature in sampling"
    )

    args = parser.parse_args()
    config = args.config
    with open(args.prefixes) as f:
        prefixes = [json.loads(line)["prefix"] for line in f]
    max_new_tokens = args.max_new_tokens
    temperature = args.temperature

    # initialize tokenizer and model
    model_path = os.path.join(config.output_dir, "model.pt")
    assert os.path.exists(model_path), f"no model checkpoint at {model_path}"
    tokenizer = tiktoken.get_encoding(config.tokenizer_encoding)
    device = determine_device() if config.device == "auto" else config.device
    model = DecoderLM(tokenizer.n_vocab, **config.model_config).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))

    # generate and save outputs
    model.eval()
    generations = generate(
        model,
        device,
        tokenizer,
        prefixes,
        config.batch_size,
        max_new_tokens,
        temperature,
    )

    generation_path = os.path.join(config.output_dir, "generation.jsonl")
    print(f"writing generations to {generation_path}")
    with open(generation_path, "w") as f:
        for prefix, generation in zip(prefixes, generations):
            json.dump({"prefix": prefix, "generation": generation}, f)
            f.write("\n")

    print("done!")


if __name__ == "__main__":
    main()
