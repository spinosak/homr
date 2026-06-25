import streamlit as st
import tempfile
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdf2image import convert_from_path
from homr.main import process_image, ProcessingConfig
from homr.music_xml_generator import XmlGeneratorArguments
import subprocess

st.title("Sheet Music Transcriber")
st.write("Upload a PDF of sheet music and get back a MusicXML file you can edit in MuseScore.")

output_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "output")

# User Interface
uploaded_file = st.file_uploader("Upload your sheet music PDF", type="pdf")

if not uploaded_file:
    st.session_state.output_xml = None
    st.session_state.last_file = None

if uploaded_file and st.session_state.get("last_file") != uploaded_file.name:
    st.session_state.output_xml = None  # Clear previous output
    st.session_state.last_file = uploaded_file.name
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder, exist_ok=True)

if uploaded_file and not st.session_state.get("output_xml"):
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Save uploaded PDF to temp location
        pdf_path = os.path.join(tmp_dir, uploaded_file.name)
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.read())

        pdf_name = os.path.splitext(uploaded_file.name)[0]
        pages_folder = os.path.join(tmp_dir, "pages")
        os.makedirs(pages_folder, exist_ok=True)

        with st.spinner("Converting PDF to images..."):
            pages = convert_from_path(pdf_path, dpi=300)
            if len(pages) == 0:                    
                st.error("This PDF appears to be blank. Please upload a PDF with sheet music.")
                st.stop()
            for index, page in enumerate(pages):
                page.save(os.path.join(pages_folder, f"page_{index + 1}.png"), "PNG")

        config = ProcessingConfig(
            enable_debug=False,
            enable_cache=False,
            write_staff_positions=False,
            read_staff_positions=False,
            selected_staff=-1,
            transformer_use_gpu=False,
            segnet_use_gpu=False,
            coreml_encoder=None
        )

        with st.spinner("Reading sheet music (this takes a moment)..."):
            progress_text = st.empty()
            for i, filename in enumerate(sorted(os.listdir(pages_folder))):
                if filename.endswith(".png"):
                    progress_text.write(f"Processing page {i + 1} of {len(pages)}...")
                    filepath = os.path.join(pages_folder, filename)
                    try:
                        process_image(filepath, config, XmlGeneratorArguments())
                    except Exception as e:
                        st.warning(f"Page {filename} doesn't appear to contain sheet music — skipping.")

        with st.spinner("Merging pages..."):
            xml_files = sorted([
                os.path.join(pages_folder, f)
                for f in os.listdir(pages_folder)
                if f.endswith(".musicxml")
            ])
            output_xml = os.path.join(output_folder, f"{pdf_name}.musicxml")
            homr_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            subprocess.run(["poetry", "run", "relieur"] + xml_files + ["-o", output_xml], cwd=homr_folder)

        if os.path.exists(output_xml):
            st.session_state.output_xml = output_xml
        else: 
            st.error("Something went wrong. No output file was generated.")

# output and download
if st.session_state.get("output_xml") and os.path.exists(st.session_state.output_xml):
    with open(st.session_state.output_xml, "rb") as f:
        st.download_button(
            label="Download MusicXML",
            data=f,
            file_name=os.path.basename(st.session_state.output_xml),
            mime="application/xml"
        )
    st.success("Done! Click the button above to download your MusicXML file.")