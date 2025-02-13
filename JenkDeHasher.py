import re
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Dict, Set
from pathlib import Path
import concurrent.futures
import logging
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1024)
def joaat_hash(text: str) -> str:
    """
    Calculate Jenkins one-at-a-time hash for a given string.
    Now cached for better performance with repeated strings.
    """
    hash_value = 0
    for char in text.lower():
        hash_value = (hash_value + ord(char)) & 0xFFFFFFFF
        hash_value = (hash_value + (hash_value << 10)) & 0xFFFFFFFF
        hash_value = (hash_value ^ (hash_value >> 6)) & 0xFFFFFFFF
    
    hash_value = (hash_value + (hash_value << 3)) & 0xFFFFFFFF
    hash_value = (hash_value ^ (hash_value >> 11)) & 0xFFFFFFFF
    hash_value = (hash_value + (hash_value << 15)) & 0xFFFFFFFF
    
    return f"hash_{hash_value:08X}"

class XMLHashProcessor:
    def __init__(self):
        self.nametable: Dict[str, str] = {}
        self.hash_pattern = re.compile(r"hash_[0-9A-Fa-f]{8}")
        
    def load_nametable(self, filepath: Path) -> None:
        """Load and process the nametable file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self.nametable = {
                    joaat_hash(line.strip()): line.strip()
                    for line in f
                    if line.strip()
                }
            logger.info(f"Loaded {len(self.nametable)} entries from nametable")
        except Exception as e:
            logger.error(f"Error loading nametable: {e}")
            raise

    def process_xml_file(self, xml_file: Path) -> None:
        """Process a single XML file."""
        try:
            with open(xml_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Process content using the precompiled regex
            new_content = self.hash_pattern.sub(
                lambda m: self.nametable.get(m.group(0), m.group(0)),
                content
            )

            # Only write if content has changed
            if new_content != content:
                with open(xml_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                logger.info(f"Processed {xml_file.name}")
            else:
                logger.info(f"No changes needed for {xml_file.name}")

        except Exception as e:
            logger.error(f"Error processing {xml_file}: {e}")
            raise

    def process_files(self, xml_files: list[Path]) -> None:
        """Process multiple XML files in parallel."""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            list(executor.map(self.process_xml_file, xml_files))

def create_file_dialog() -> tk.Tk:
    """Create and configure the file dialog window."""
    root = tk.Tk()
    root.withdraw()
    return root

def main():
    try:
        root = create_file_dialog()
        
        # Select nametable file
        nametable_path = filedialog.askopenfilename(
            title="Select the NameTable file",
            filetypes=[("Text Files", "*.txt")]
        )
        if not nametable_path:
            logger.info("No nametable file selected. Exiting.")
            return

        # Select XML files
        xml_paths = filedialog.askopenfilenames(
            title="Select XML files to process",
            filetypes=[("XML Files", ("*.ytyp.xml", "*.ymap.xml"))]
        )
        if not xml_paths:
            logger.info("No XML files selected. Exiting.")
            return

        # Initialize processor and process files
        processor = XMLHashProcessor()
        processor.load_nametable(Path(nametable_path))
        processor.process_files([Path(p) for p in xml_paths])

        messagebox.showinfo("Success", "Processing completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
    finally:
        root.destroy()

if __name__ == "__main__":
    main()