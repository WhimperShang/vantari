"""
remove_random_pages.py
───────────────────────────────────────────────────────────────────────────────
Takes scanned answer-paper PDFs, randomly removes a few pages,
and encodes the removed page numbers into the output filename. (used for testing)

USAGE
    python remove_random_pages.py <input.pdf> [options] # for a single file
    python remove_random_pages.py <input_folder> [options] # for all PDFs in a folder

    Run "python remove_random_pages.py --help" for all options, including:

    --num-remove / -n       Number of pages to remove (default: 2)
    --output-dir / -o       Directory to save output (default: same as input)
    --seed / -s             Random seed for reproducibility (optional)

OUTPUT FILENAME EXAMPLE
    StudentA_answers.pdf  →  StudentA_answers_MISSING_p3_p7.pdf

DEPENDENCIES
    pip install pymupdf
"""

# ── Imports ──────────────────────────────────────────────────────────────────

import argparse
import random
import sys
from pathlib import Path

try:
    import fitz
except ImportError:
    print("fitz not found. Install it with:  pip install pymupdf")
    sys.exit(1)

# ── Helpers ──────────────────────────────────────────────────────────────────

def generate_new_name(
    input_path: Path, 
    removed_pages: list[int],
    ) -> str:

    *head, tail = removed_pages
    missing_tag = ", ".join(str(n) for n in head) + (f" & {tail}" if head else str(tail))
        
    return f"{input_path.stem} (missing {missing_tag}){input_path.suffix}"

def remove_random_pages(
    input_path: Path,
    output_dir: Path,
    rng: random.Random,
    num_remove: int = 2,
) -> Path | None:
    
    """
    Remove `num_remove` randomly selected pages from a PDF and save it
    with the missing page numbers encoded in the filename.

    Args:
        input_path: Path to the source PDF file.
        output_dir: Directory to write the output PDF.
        rng: Random instance to use for page selection.
        num_remove: Number of pages to remove (default: 2).

    Returns:
        Path to the output PDF, or None if the file was skipped.
    """
    
    doc = fitz.open(str(input_path))
    total_pages = len(doc)

    if total_pages <= num_remove:
        print(
            f"  ⚠  Skipping '{input_path.name}': only {total_pages} page(s), can't remove {num_remove}."
        )
        doc.close()
        return None

    removed_indices = sorted(rng.sample(range(total_pages), num_remove))
    removed_pages_1indexed = [i + 1 for i in removed_indices]

    # Delete in reverse order so indices don't shift as pages are removed
    for i in reversed(removed_indices):
        doc.delete_page(i)

    new_name = generate_new_name(input_path, removed_pages_1indexed)
    output_path = output_dir / new_name

    doc.save(str(output_path))
    doc.close()

    kept = total_pages - num_remove
    print(
        f"  ✓  {input_path.name}  →  {new_name}\n"
        f"     Removed page(s): {removed_pages_1indexed}  |  "
        f"Kept {kept}/{total_pages} pages"
    )
    return output_path

# ── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Takes scanned answer-paper PDFs, randomly removes a few pages,"
                    "and encodes the removed page numbers into the output filename. (used for testing)"
    )
    parser.add_argument(
        "input",
        help="Path to a single PDF file OR a directory containing PDF files.",
    )
    parser.add_argument(
        "--num-remove", "-n",
        type=int,
        default=2,
        metavar="N",
        help="Number of pages to remove per PDF (default: 2).",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        metavar="DIR",
        help="Directory to write output PDFs (default: same as input file/folder).",
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Random seed for reproducibility (optional).",
    )
    return parser.parse_args()

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    input_path = Path(args.input)
    rng = random.Random(args.seed)

    # Collect PDF files to process
    if input_path.is_dir():
        pdf_files = sorted(input_path.glob("*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in '{input_path}'.")
            sys.exit(1)
        default_output_dir = input_path
    elif input_path.is_file() and input_path.suffix.lower() == ".pdf":
        pdf_files = [input_path]
        default_output_dir = input_path.parent
    else:
        print(f"Error: '{input_path}' is not a PDF file or a directory.")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nProcessing {len(pdf_files)} file(s) → output dir: {output_dir}\n")

    success, skipped = 0, 0
    for pdf in pdf_files:
        result = remove_random_pages(pdf, output_dir, rng, args.num_remove)
        if result:
            success += 1
        else:
            skipped += 1

    print(f"\nDone. {success} processed, {skipped} skipped.")

if __name__ == "__main__":
    main()