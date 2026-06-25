import sys
import os
import subprocess
from pdf2image import convert_from_path
from homr.main import process_image, ProcessingConfig
from homr.music_xml_generator import XmlGeneratorArguments
from relieur.relieur import main as relieur_merge

# Get the PDF path from the command line
pdf_path = sys.argv[1]

# Get the PDF name without extension e.g. "myscore"
pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

# Create folder structure
script_folder = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(script_folder, "output", pdf_name)
pages_folder = os.path.join(output_folder, "pages")
os.makedirs(pages_folder, exist_ok=True)

# Convert PDF pages to PNGs
print(f"Converting {pdf_name}.pdf to images...")
pages = convert_from_path(pdf_path, dpi=300)

for index, page in enumerate(pages):
    filename = f"page_{index + 1}.png"
    filepath = os.path.join(pages_folder, filename)
    page.save(filepath, "PNG")

print(f"Saved {len(pages)} pages to {pages_folder}")

# Create HOMR config once before the loop
config = ProcessingConfig(
    enable_debug=False,
    enable_cache=False,
    write_staff_positions=False,
    read_staff_positions=False,
    selected_staff=-1,
    use_gpu_inference=False
)

# Run HOMR on each PNG
print("Running HOMR on each page...")
for filename in sorted(os.listdir(pages_folder)):
    if filename.endswith(".png"):
        filepath = os.path.join(pages_folder, filename)
        print(f"Processing {filename}...")
        process_image(filepath, config, XmlGeneratorArguments())

# Merge all XMLs into one
print("Merging XML files...")
xml_files = sorted([
    os.path.join(pages_folder, f)
    for f in os.listdir(pages_folder)
    if f.endswith(".musicxml")
])

output_xml = os.path.join(output_folder, f"{pdf_name}.musicxml")
subprocess.run(["poetry", "run", "relieur"] + xml_files + ["-o", output_xml], cwd="/Users/karenspinosa/Documents/homr")

print(f"Done! Your MusicXML file is at: {output_xml}")