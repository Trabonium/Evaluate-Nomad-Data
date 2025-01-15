import os
from PIL import Image  # Für die Bildverarbeitung
from pptx import Presentation
from pptx.util import Inches

def extract_images_from_pdf(pdf_path, output_folder):
    from PyMuPDF import open as fitz_open  # PyMuPDF

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

def duplicate_slide(prs, slide_index):
    """Dupliziert eine Folie und gibt die neue Folie zurück."""
    slide = prs.slides[slide_index]
    slide_layout = slide.slide_layout  # Behalte das Layout der ursprünglichen Folie

    # Neue Folie basierend auf dem gleichen Layout erstellen
    new_slide = prs.slides.add_slide(slide_layout)

    # Shapes (Inhalte) der Originalfolie kopieren
    for shape in slide.shapes:
        if shape.is_placeholder:
            continue  # Platzhalter überspringen, da sie bereits im Layout enthalten sind

        if shape.shape_type == 1:  # Textfeld
            new_shape = new_slide.shapes.add_textbox(
                shape.left, shape.top, shape.width, shape.height
            )
            new_shape.text = shape.text  # Text kopieren
        elif shape.shape_type == 13:  # Bild
            new_slide.shapes.add_picture(
                shape.image.blob, shape.left, shape.top, shape.width, shape.height
            )
        # Füge hier weitere Typen hinzu, wenn nötig

    return new_slide

def insert_images_into_ppt(ppt_path, image_paths, output_ppt_path):
    prs = Presentation(ppt_path)

    # Sicherstellen, dass mindestens 3 Folien vorhanden sind
    if len(prs.slides) < 3:
        slide_layout = prs.slide_layouts[1]
        for _ in range(3 - len(prs.slides)):
            prs.slides.add_slide(slide_layout)

    third_slide_index = 2  # Index von Folie 3

    # Definierter Bereich für das Bild (z. B. maximal 5 x 4 Inches)
    max_width = Inches(5)
    max_height = Inches(4)

    for idx, image_path in enumerate(image_paths):
        # Bilddimensionen laden
        with Image.open(image_path) as img:
            img_width, img_height = img.size

        # Verhältnis berechnen
        img_ratio = img_width / img_height
        max_ratio = max_width / max_height

        if img_ratio > max_ratio:
            new_width = max_width
            new_height = max_width / img_ratio
        else:
            new_height = max_height
            new_width = max_height * img_ratio

        # Position berechnen (bündig rechts und vertikal zentriert)
        left = Inches(10) - new_width
        top = (Inches(7.5) - new_height) / 2

        if idx == 0:
            # Erstes Bild auf der dritten Folie einfügen
            third_slide = prs.slides[third_slide_index]
            third_slide.shapes.add_picture(image_path, left, top, width=new_width, height=new_height)
        else:
            # Folie 3 duplizieren und Bild einfügen
            new_slide = duplicate_slide(prs, third_slide_index)
            new_slide.shapes.add_picture(image_path, left, top, width=new_width, height=new_height)

    prs.save(output_ppt_path)

def Beginn():
    pdf_path = "your_pdf_file.pdf"  # Pfad zur PDF-Datei
    ppt_path = "ELN_Training_Taskforce.pptx"  # Pfad zur PowerPoint-Vorlage
    output_folder = "extracted_images"  # Ordner für extrahierte Bilder
    output_ppt_path = "output_presentation.pptx"  # Pfad zur gespeicherten Präsentation

    # Sicherstellen, dass der Ausgabeordner existiert
    os.makedirs(output_folder, exist_ok=True)

    # Bilder aus der PDF extrahieren
    image_paths = extract_images_from_pdf(pdf_path, output_folder)

    # Bilder in die PowerPoint-Präsentation einfügen
    insert_images_into_ppt(ppt_path, image_paths, output_ppt_path)

    print(f"Präsentation wurde erstellt: {output_ppt_path}")

