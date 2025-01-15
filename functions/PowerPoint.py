import os
from PIL import Image  # Für die Bildverarbeitung
from pptx import Presentation
from pptx.util import Inches
from fitz import open as fitz_open  # PyMuPDF
from tkinter import Tk, filedialog

def extract_images_from_pdf(pdf_path, output_folder):
    """Extrahiert Bilder aus einer PDF-Datei und speichert sie im Ausgabeverzeichnis."""
    pdf_document = fitz_open(pdf_path)
    image_paths = []

    for page_number in range(len(pdf_document)):
        page = pdf_document[page_number]
        images = page.get_images(full=True)

        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_extension = base_image["ext"]
            image_filename = f"page{page_number + 1}_img{img_index + 1}.{image_extension}"
            image_path = os.path.join(output_folder, image_filename)

            with open(image_path, "wb") as image_file:
                image_file.write(image_bytes)

            image_paths.append(image_path)

    pdf_document.close()
    return image_paths


def create_presentation(image_paths, output_ppt_path):
    """Erstellt eine PowerPoint-Präsentation und fügt extrahierte Bilder hinzu."""
    prs = Presentation()

    # Folie 3 erstellen oder duplizieren
    slide_layout = prs.slide_layouts[5]  # Leere Folie
    slide = prs.slides.add_slide(slide_layout)  # Leere Folie 1
    slide = prs.slides.add_slide(slide_layout)  # Leere Folie 2
    slide = prs.slides.add_slide(slide_layout)  # Leere Folie 3

    max_width = Inches(5)
    max_height = Inches(4)
    right_edge = Inches(10)  # Rechte Kante der Folie

    # Bilder auf Folie 3 einfügen und duplizieren
    for idx, image_path in enumerate(image_paths):
        # Folie 3 einfügen/duplizieren je nach Bildanzahl
        if idx > 0:
            slide = prs.slides.add_slide(slide_layout)  # Folie 3 duplizieren
        left = right_edge - max_width
        top = (Inches(7.5) - max_height) / 2  # Zentriert
        slide.shapes.add_picture(image_path, left, top, width=max_width, height=max_height)

    prs.save(output_ppt_path)
    print(f"PowerPoint-Datei wurde gespeichert: {output_ppt_path}")


def process_pdf_to_ppt(pdf_path, pdf_filename):
    """Hauptprozess: Extrahiert Bilder aus der PDF und erstellt eine PowerPoint-Präsentation."""
    output_folder = os.path.dirname(pdf_path)

    # Template.pptx laden oder Datei auswählen
    template_ppt_path = os.path.join(output_folder, "Template.pptx")
    if not os.path.exists(template_ppt_path):
        print("Template.pptx nicht gefunden. Bitte wähle die Datei aus.")
        Tk().withdraw()  # Verhindert, dass das Tkinter-Hauptfenster angezeigt wird
        template_ppt_path = filedialog.askopenfilename(title="Template.pptx auswählen", filetypes=[("PowerPoint-Dateien", "*.pptx")])

    if not template_ppt_path:
        print("Es konnte keine Template.pptx-Datei gefunden oder ausgewählt werden.")
        return

    # Extrahieren der Bilder
    print("Extrahiere Bilder aus der PDF...")
    image_paths = extract_images_from_pdf(pdf_path+"/"+pdf_filename, output_folder)
    if not image_paths:
        print("Keine Bilder in der PDF gefunden.")
        return

    # Erstellen der PowerPoint-Präsentation
    output_ppt_path = os.path.join(output_folder, "output_presentation.pptx")
    print("Erstelle PowerPoint-Präsentation...")
    create_presentation(image_paths, output_ppt_path)
