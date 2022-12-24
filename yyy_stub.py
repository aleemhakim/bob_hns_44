# Description: PDF scraper
# Author: Anthony Batista
# Website: www.entkreis.com
# Last modified: 2022-08-05
# Revision: 3

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.high_level import extract_text
import glob

from pdf2image import convert_from_path

import matplotlib.pyplot as plt
import cv2 as cv
import numpy as np

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LTTextBox, LTTextLine, LTFigure, LTTextBoxHorizontal
from collections import defaultdict

import pandas as pd
import re
import os

from datetime import datetime

################################################
# Read templates for checkboxes
tmpl_checked = []
tmpl_unchecked = []

for fn in glob.glob("templates/checked/*.png"):
  tmpl_checked.append(cv.imread(fn, cv.IMREAD_GRAYSCALE))

for fn in glob.glob("templates/unchecked/*.png"):
  tmpl_unchecked.append(cv.imread(fn, cv.IMREAD_GRAYSCALE))

################################################
# Search for pdfs

pdfs = glob.glob("input/**/*.pdf", recursive=True)

################################################
# Create output directory
os.makedirs("output", exist_ok=True)


################################################
# DataFrame for all
df_all = pd.DataFrame()

################################################
# Iterate through every pdf
for i, pdf in enumerate(pdfs):
  print(f"PDF {i+1}/{len(pdfs)} {pdf}")

  ################################################
  # Convert PDF to images

  # Resave so that pdf2image doesn't run into
  # weird filename encoding issues
  f = open(pdf, "rb")
  content = f.read()

  tmp = open("tmp.pdf", "wb")
  tmp.write(content)
  tmp.close()

  pages = convert_from_path("tmp.pdf")
  pages_img = []
  for i, page in enumerate(pages):
    page.save(f"page{i+1}.png", "png")
    pages_img.append(cv.imread(f"page{i+1}.png", cv.IMREAD_GRAYSCALE))

  ################################################
  # Open PDF for text extraction
  fp = open(pdf, 'rb')
  parser = PDFParser(fp)
  doc = PDFDocument(parser)
  rsrcmgr = PDFResourceManager()
  laparams = LAParams()
  device = PDFPageAggregator(rsrcmgr, laparams=laparams)
  interpreter = PDFPageInterpreter(rsrcmgr, device)

  pages = list(iter(PDFPage.create_pages(doc)))

  ################################################
  # Function to collect all text blocks
  texts = []

  def parse_layout(layout):
    global texts
    for lt_obj in layout:
      if isinstance(lt_obj, LTTextBoxHorizontal):
        texts.append((
          (lt_obj.x0, lt_obj.x1, lt_obj.y0, lt_obj.y1),
          lt_obj.get_text()))
      elif isinstance(lt_obj, LTFigure):
        parse_layout(lt_obj)

  ################################################
  # Function to search for text block at coordinates
  def get_text_at(x0, x1, y0, y1):
    for ((_x0, _x1, _y0, _y1), text) in texts:
      x_overlap = False
      if x0 <= _x0 and x1 >= _x0:
        x_overlap = True

      if x0 <= _x1 and x1 >= _x1:
        x_overlap = True

      if x0 >= _x1 and x1 <= _x1:
        x_overlap = True

      y_overlap = False
      if y0 <= _y0 and y1 >= _y0:
        y_overlap = True

      if y0 <= _y1 and y1 >= _y1:
        y_overlap = True

      if y0 >= _y1 and y1 <= _y1:
        y_overlap = True

      if x_overlap and y_overlap:
        return text
    return ""

  ################################################
  # Function to get text at position (extended)
  def get_text_at_ext(x0, x1, y0, y1, flag=""):
    candidates = []
    for ((_x0, _x1, _y0, _y1), text) in texts:
      x_overlap = False
      if x0 <= _x0 and x1 >= _x0:
        x_overlap = True

      if x0 <= _x1 and x1 >= _x1:
        x_overlap = True

      if x0 >= _x0 and x1 <= _x1:
        x_overlap = True

      y_overlap = False
      if y0 <= _y0 and y1 >= _y0:
        y_overlap = True

      if y0 <= _y1 and y1 >= _y1:
        y_overlap = True

      if y0 >= _y0 and y1 <= _y1:
        y_overlap = True

      if x_overlap and y_overlap:
        candidates.append(((round(_x0), round(_x1), round(_y0), round(_y1)), text))
    if len(candidates) > 0:
      if flag == "left":
        idx = np.argmin([x0 for ((x0, _, _, _), _) in candidates])
      elif flag == "top":
        idx = np.argmin([y0 for ((_, _, y0, _), _) in candidates])
      else:
        idx = 0
      return candidates[idx]

    return None, ""

  ################################################
  # Function to get table in PDF
  def get_table(x0, x1, y0, y1, max_width, max_height, max_rows=100):
    rows = []

    pos, text = get_text_at_ext(x0, x1, y0, y1)
    first_pos = pos

    row = []
    row.append(text)

    for i in range(max_rows):
      while True:
        pos, text = get_text_at_ext(pos[1]+2, pos[1]+2+max_width, pos[2], pos[3], "left")
        if pos is None:
          break
        row.append(text)

      # Dummy inputs
      for _ in range(10):
        row.append("")

      rows.append(row)
      row = []
      pos, text = get_text_at_ext(
          first_pos[0], first_pos[1],
          first_pos[2]-2-max_height, first_pos[2]-2, "top")
      first_pos = pos
      if pos is None:
        break
      row.append(text)


    return rows

  ################################################
  # Function to detect checkboxes on page
  # with OpenCV
  def detect_checkboxes(img, tmpl_checked, tmpl_unchecked):
    checkboxes = []

    def detect(img, tmpl_list, txt, checkboxes):
      for tmpl in tmpl_list:
        res = cv.matchTemplate(img, tmpl, cv.TM_CCOEFF_NORMED)

        good = np.zeros(res.shape, np.uint8)
        good[res > 0.7] = 255

        num_labels, _, stats, _ =  cv.connectedComponentsWithStats(good, 4, cv.CV_32S)

        for i in range(1, num_labels):
          x = stats[i, cv.CC_STAT_LEFT] + stats[i, cv.CC_STAT_WIDTH]//2
          y = stats[i, cv.CC_STAT_TOP] + stats[i, cv.CC_STAT_HEIGHT]//2
          checkboxes.append((
            (x*72//200, (x+tmpl.shape[1])*72//200, (img.shape[0] - (y+tmpl.shape[0]))*72//200, (img.shape[0] - y)*72//200),
            txt))

    detect(img, tmpl_checked, "Ja", checkboxes)
    detect(img, tmpl_unchecked, "Nein", checkboxes)

    return checkboxes

  ################################################
  # Function to check if a checkbox is checked or not
  def is_checked(img, x0, y0, size=30):
    return np.sum(255 - img[y0:y0+size,x0:x0+size])/(size*size) > 55

  # 4 Page format
  if len(pages) == 4:
    ################################################
    # Page 1
    texts = []
    interpreter.process_page(pages[0])
    parse_layout(device.get_result())

    row = defaultdict(lambda x: "")

    # Objektnummer
    txt = get_text_at(330, 463, 681, 693)
    m = re.search(r'\d+', txt)
    row["Objektnummer"] = m.group(0)

    # Adresse
    txt = get_text_at(193, 368, 665, 675)
    row["Adresse"] = txt

    # Gebäudetyp
    txt = get_text_at(193, 272, 644, 654)
    row["Gebäudetyp"] = txt

    # Gebäudeteil
    txt = get_text_at(193, 272, 624, 633)
    row["Gebäudeteil"] = txt

    # Baujahr Gebäude
    txt = get_text_at(193, 216, 604, 614)
    row["Baujahr Gebäude"] = txt

    # Anzahl Wohnungen
    txt = get_text_at(193, 199, 563, 573)
    row["Anzahl Wohnungen"] = txt

    # Gebäudenutzfläche (AN)
    txt = get_text_at(193, 210, 543, 553)
    row["Gebäudenutzfläche (AN)"] = txt

    # Wesentliche Energieträger für Heizung und Warmwasser
    txt = get_text_at(193, 235, 523, 533)
    row["Wesentliche Energieträger für Heizung und Warmwasser"] = txt

    # Erneuerbare Energien (Art)
    txt = get_text_at(209, 220, 503, 511)
    row["Erneuerbare Energien (Art)"] = txt

    # Erneuerbare Energien (Verwendung)
    txt = get_text_at(420, 430, 503, 511)
    row["Erneuerbare Energien (Verwendung)"] = txt

    # Art der Lüftung/Kühlung
    row["Art der Lüftung/Kühlung"] = []
    if is_checked(pages_img[0], 545, 967):
      row["Art der Lüftung/Kühlung"].append("Fensterlüftung")
    if is_checked(pages_img[0],545, 1003):
      row["Art der Lüftung/Kühlung"].append("Schachtlüftung")
    if is_checked(pages_img[0],755, 967):
      row["Art der Lüftung/Kühlung"].append("Lüftungsanlage mit Wärmerückgewinnung")
    if is_checked(pages_img[0],755, 1003):
      row["Art der Lüftung/Kühlung"].append("Lüftungsanlage ohne Wärmerückgewinnung")
    if is_checked(pages_img[0],1275, 967):
      row["Art der Lüftung/Kühlung"].append("Anlage zur Kühlung")

    # Anlass der Ausstellung des Energieausweises
    row["Anlass der Ausstellung des Energieausweises"] = []
    if is_checked(pages_img[0],571, 1056):
      row["Anlass der Ausstellung des Energieausweises"].append("Neubau")
    if is_checked(pages_img[0],571, 1088):
      row["Anlass der Ausstellung des Energieausweises"].append("Vermietung/Verkauf")
    if is_checked(pages_img[0],899, 1056):
      row["Anlass der Ausstellung des Energieausweises"].append("Modernisierung (Änderung/Erweiterung)")
    if is_checked(pages_img[0],1150, 1056):
      row["Anlass der Ausstellung des Energieausweises"].append("Sonstiges (freiwillig)")


    ################################################
    # Page 2
    texts = []
    interpreter.process_page(pages[1])
    parse_layout(device.get_result())

    # Endenergieverbrauch dieses Gebäudes
    txt = get_text_at(207, 394, 649, 674)
    txt = txt.splitlines()[1]
    row["Endenergieverbrauch dieses Gebäudes"] = txt

    # Primärenergieverbrauch dieses Gebäudes
    txt = get_text_at(200, 400, 522, 545)
    txt = txt.splitlines()[0]
    row["Primärenergieverbrauch dieses Gebäudes"] = txt

    # Endenergieverbrauch dieses Gebäudes [Pflichtangabe für Immobilienanzeigen]
    txt = get_text_at(427, 518, 492, 504)
    row["Endenergieverbrauch dieses Gebäudes [Pflichtangabe für Immobilienanzeigen]"] = txt

    # Read table
    row["Verbrauchserfassung"] = []

    for i in range(4):
      rowrow = {}
      off = i*13

      # Abrechnungszeitraum (von)
      txt = get_text_at(151, 185, 380-off, 387-off)
      rowrow["Abrechnungszeitraum (von)"] = txt

      # Abrechnungszeitraum (bis)
      txt = get_text_at(199, 233, 380-off, 387-off)
      rowrow["Abrechnungszeitraum (bis)"] = txt

      # Primärenergieverbrauch [kWh/m²]
      txt = get_text_at(254, 275, 380-off, 387-off)
      rowrow["Primärenergieverbrauch [kWh/m²]"] = txt

      # Energieverbrauch [kWh]
      txt = get_text_at(298, 319, 380-off, 387-off)
      rowrow["Energieverbrauch [kWh]"] = txt

      # Anteil Warmwasser [kWh]
      txt = get_text_at(338, 358, 380-off, 387-off)
      rowrow["Anteil Warmwasser [kWh]"] = txt

      # Anteil Heizung [kWh]
      txt = get_text_at(384, 403, 380-off, 387-off)
      rowrow["Anteil Heizung [kWh]"] = txt

      # Klimafaktor
      txt = get_text_at(437, 450, 380-off, 387-off)
      rowrow["Klimafaktor"] = txt

      # Kennwert [kWh/m²]
      txt = get_text_at(487, 499, 380-off, 387-off)
      rowrow["Kennwert [kWh/m²]"] = txt

      row["Verbrauchserfassung"].append(rowrow)

    ################################################
    # Page 3
    texts = []
    interpreter.process_page(pages[2])
    parse_layout(device.get_result())

    # Möglichkeit zur Verbesserung der Energieeffizienz
    row["Möglichkeit zur Verbesserung der Energieeffizienz"] = ""
    if is_checked(pages_img[2], 1043, 422):
      row["Möglichkeit zur Verbesserung der Energieeffizienz"] = "möglich"
    if is_checked(pages_img[2], 1267, 426):
      row["Möglichkeit zur Verbesserung der Energieeffizienz"] = "nicht möglich"


    # Read table
    row["Empfehlungen zur kostengünstigen Modernisierung"] = []

    for i in range(6):
      rowrow = {}
      off = i*12

      # Nr. Bau- oder Anlagenteile
      txt = get_text_at(76, 115, 601-off, 609-off)
      txt = " ".join(txt.split()[1:])
      rowrow["Nr. Bau- oder Anlagenteile"] = txt

      # Maßnahmenbeschreibung in einzelnen Schritten
      txt = get_text_at(193, 339, 601-off, 609-off)
      rowrow["Maßnahmenbeschreibung in einzelnen Schritten"] = txt

      # größerer Modernisierung
      if is_checked(pages_img[2], 1216, 642+i*34, 20):
        rowrow["größerer Modernisierung"] = "empfohlen"
      else:
        rowrow["größerer Modernisierung"] = "nicht empfohlen"


      # Einzelmaßnahme
      if is_checked(pages_img[2], 1369, 642+i*34, 20):
        rowrow["Einzelmaßnahme"] = "empfohlen"
      else:
        rowrow["Einzelmaßnahme"] = "nicht empfohlen"

      row["Empfehlungen zur kostengünstigen Modernisierung"].append(rowrow)

  # 1 Page format
  elif len(pages) == 1:
    ################################################
    # Page 1
    texts = []
    interpreter.process_page(pages[0])
    parse_layout(device.get_result())

    row = defaultdict(lambda: "")

    # Objektnummer
    txt = get_text_at(390, 522, 665, 677)
    m = re.search(r'\d+', txt)
    row["Objektnummer"] = m.group(0)

    # Adresse
    txt = get_text_at(182, 283, 633, 641)
    row["Adresse"] = txt

    # Gebäudetyp
    txt = get_text_at(182, 246, 650, 659)
    row["Gebäudetyp"] = txt

    # Gebäudeteil
    txt = get_text_at(182, 236, 615, 623)
    row["Gebäudeteil"] = txt

    # Baujahr Gebäude
    txt = get_text_at(182, 200, 598, 606)
    row["Baujahr Gebäude"] = txt

    # Anzahl Wohnungen
    txt = get_text_at(182, 187, 563, 571)
    row["Anzahl Wohnungen"] = txt

    # Gebäudenutzfläche (AN)
    txt = get_text_at(182, 215, 545, 553)
    row["Gebäudenutzfläche (AN)"] = txt

    # Wesentliche Energieträger für Heizung und Warmwasser
    txt = get_text_at(182, 216, 526, 533)
    row["Wesentliche Energieträger für Heizung und Warmwasser"] = txt

    # Erneuerbare Energien (Art)
    txt = get_text_at(196, 210, 506, 514)
    row["Erneuerbare Energien (Art)"] = txt

    # Erneuerbare Energien (Verwendung)
    txt = get_text_at(405, 420, 506, 514)
    row["Erneuerbare Energien (Verwendung)"] = txt

    # Endenergieverbrauch dieses Gebäudes
    txt1 = get_text_at(283, 303, 403, 411)
    txt2 = get_text_at(316, 355, 403, 411)
    row["Endenergieverbrauch dieses Gebäudes"] = f"{txt1} {txt2}"

    # Primärenergieverbrauch dieses Gebäudes
    txt1 = get_text_at(298, 318, 343, 351)
    txt2 = get_text_at(331, 370, 343, 351)
    row["Primärenergieverbrauch dieses Gebäudes"] = f"{txt1} {txt2}"

  # 5 page format
  elif len(pages) == 5:
    ################################################
    # Page 1
    texts = []
    interpreter.process_page(pages[0])
    parse_layout(device.get_result())
    texts += detect_checkboxes(pages_img[0], tmpl_checked, tmpl_unchecked)

    row = defaultdict(lambda: "")

    # Objektnummer
    txt = get_text_at(390, 522, 665, 677)
    m = re.search(r'\d+', txt)
    row["Objektnummer"] = m.group(0)

    # Gebäude
    table = get_table(63, 108, 650, 659, 150, 20, 8)
    row["Gebäudetyp"] = table[0][1]
    row["Adresse"] = table[1][1]
    row["Gebäudeteil"] = table[2][1]
    row["Baujahr Gebäude"] = table[3][1]
    row["Baujahr Wärmeerzeuger"] = table[4][1]
    row["Anzahl Wohnungen"] = table[5][1]
    row["Gebäudenutzfläche (AN)"] = table[6][1]
    row["Wesentliche Energieträger für Heizung und Warmwasser"] = table[7][1]

    # Art der Lüftung/Kühlung
    row["Art der Lüftung/Kühlung"] = []
    if is_checked(pages_img[0], 504, 954, 20):
      row["Art der Lüftung/Kühlung"].append("Fensterlüftung")
    if is_checked(pages_img[0],505, 979, 20):
      row["Art der Lüftung/Kühlung"].append("Schachtlüftung")
    if is_checked(pages_img[0],740, 954, 20):
      row["Art der Lüftung/Kühlung"].append("Lüftungsanlage mit Wärmerückgewinnung")
    if is_checked(pages_img[0],740, 979, 20):
      row["Art der Lüftung/Kühlung"].append("Lüftungsanlage ohne Wärmerückgewinnung")
    if is_checked(pages_img[0],1275, 953, 20):
      row["Art der Lüftung/Kühlung"].append("Anlage zur Kühlung")

    # Anlass der Ausstellung des Energieausweises
    row["Anlass der Ausstellung des Energieausweises"] = []
    if is_checked(pages_img[0],504, 1021):
      row["Anlass der Ausstellung des Energieausweises"].append("Neubau")
    if is_checked(pages_img[0],504, 1045):
      row["Anlass der Ausstellung des Energieausweises"].append("Vermietung/Verkauf")
    if is_checked(pages_img[0],851, 1021):
      row["Anlass der Ausstellung des Energieausweises"].append("Modernisierung (Änderung/Erweiterung)")
    if is_checked(pages_img[0],1195, 1021):
      row["Anlass der Ausstellung des Energieausweises"].append("Sonstiges (freiwillig)")

    ################################################
    # Page 2
    texts = []
    interpreter.process_page(pages[1])
    parse_layout(device.get_result())
    texts += detect_checkboxes(pages_img[1], tmpl_checked, tmpl_unchecked)

    # CO2-Emissionen
    txt1 = get_text_at(473, 489, 652, 660)
    txt2 = get_text_at(495, 529, 652, 660)
    row["CO2-Emissionen"] = f"{txt1} {txt2}"

    # Endenergiebedarf dieses Gebäudes
    txt = get_text_at(458, 530, 397, 406)
    row["Endenergiebedarf dieses Gebäudes"] = txt

    # Primärenergiebedarf dieses Gebäudes
    txt = get_text_at(100, 220, 471, 478)
    row["Primärenergiebedarf dieses Gebäudes"] = txt

    # Primärenergiebedarf (Ist-Wert)
    txt = get_text_at(100, 220, 471, 478)
    row["Primärenergiebedarf (Ist-Wert)"] = f"{txt.split()[0]} kWh/(m²·a)"

    # Primärenergiebedarf (Anforderungswert)
    txt = get_text_at(232, 288, 471, 478)
    row["Primärenergiebedarf (Anforderungswert)"] = txt

    # Energetische Qualität der Gebäudehülle HT (Ist-Wert)
    txt = get_text_at(63, 198, 446, 464)
    txt = txt.splitlines()[1]
    row["Energetische Qualität der Gebäudehülle HT (Ist-Wert)"] = txt

    # Energetische Qualität der Gebäudehülle HT (Anforderungswert)
    txt = get_text_at(232, 281, 446, 453)
    row["Energetische Qualität der Gebäudehülle HT (Anforderungswert)"] = txt

    # Sommerlicher Wärmeschutz (bei Neubau)
    def JaNein(t):
      return "Ja" if t else "Nein"
    row["Sommerlicher Wärmeschutz (bei Neubau)"] = JaNein(is_checked(pages_img[1], 590, 1117, 20))

    # Verfahren nach DIN V 4108-6 und DIN V 4701-10
    row["Verfahren nach DIN V 4108-6 und DIN V 4701-10"] = JaNein(is_checked(pages_img[1], 842, 1007, 20))

    # Verfahren nach DIN V 18599
    row["Verfahren nach DIN V 18599"] =  JaNein(is_checked(pages_img[1], 842, 1042, 20))

    # Regelung nach § 3 Absatz 5 EnEV
    row["Regelung nach § 3 Absatz 5 EnEV"] =  JaNein(is_checked(pages_img[1], 842, 1077, 20))

    # Vereinfachungen nach § 9 Abs. 2 EnEV
    row["Vereinfachungen nach § 9 Abs. 2 EnEV"] =  JaNein(is_checked(pages_img[1], 842, 1112, 20))

    ################################################
    # Page 4
    texts = []
    interpreter.process_page(pages[3])
    parse_layout(device.get_result())
    texts += detect_checkboxes(pages_img[3], tmpl_checked, tmpl_unchecked)

    table = get_table(63, 330, 650, 658, 150, 30, 1)
    row["Möglichkeit zur Verbesserung der Energieeffizienz"] = table[0][1]

    table = get_table(69, 74, 550, 558, 150, 30, 8)
    row["Empfehlungen zur kostengünstigen Modernisierung"] = []
    for table_row in table:
      if len(table_row) >= 5:
        rowrow = {}

        # Bau- oder Anlagenteile
        rowrow["Bau- oder Anlagenteile"] = table_row[1]

        # Maßnahmenbeschreibung in einzelnen Schritten
        rowrow["Maßnahmenbeschreibung in einzelnen Schritten"] = table_row[2]

        # in Zusammenhang mit größerer Modernisierung
        rowrow["in Zusammenhang mit größerer Modernisierung"] = table_row[3]

        # als Einzelmaßnahme
        rowrow["als Einzelmaßnahme"] = table_row[4]

        row["Empfehlungen zur kostengünstigen Modernisierung"].append(rowrow)
      else:
        break



  ################################################
  # Generate Excel

  # Read template excel
  df = pd.read_excel("Excel output.xlsx", "Sheet1")
  df = df.append({}, ignore_index=True)
  df = df.fillna('')
  original_df = df.copy()


  # Function to fill at placeholder
  not_filled = list(range(1, 42))
  def fill_placeholder(df, id, val, offset_row=0):
    if id in not_filled:
      not_filled.remove(id)
    idx = np.argwhere((original_df == id).to_numpy())
    df.iat[idx[0][0]+offset_row, idx[0][1]] = val

  def fill_empty(df):
    for id in not_filled:
      idx = np.argwhere((original_df == id).to_numpy())
      df.iat[idx[0][0], idx[0][1]] = ""

  fname = os.path.basename(pdf)
  fname = os.path.splitext(fname)[0]
  fill_placeholder(df, 1, fname)
  fill_placeholder(df, 2, row["Objektnummer"])
  fill_placeholder(df, 3, row["Adresse"])
  fill_placeholder(df, 4, row["Gebäudetyp"])
  fill_placeholder(df, 5, row["Gebäudeteil"])
  fill_placeholder(df, 6, row["Baujahr Gebäude"])
  fill_placeholder(df, 7, row["Anzahl Wohnungen"])
  fill_placeholder(df, 8, row["Gebäudenutzfläche (AN)"])
  fill_placeholder(df, 9, row["Wesentliche Energieträger für Heizung und Warmwasser"])
  fill_placeholder(df, 10, "Art: " + row["Erneuerbare Energien (Art)"] + " Verwendung: " + row["Erneuerbare Energien (Verwendung)"])

  if len(pages) == 4:

    fill_placeholder(df, 11, ", ".join(row["Art der Lüftung/Kühlung"]))
    fill_placeholder(df, 12, ", ".join(row["Anlass der Ausstellung des Energieausweises"]))

    fill_placeholder(df, 13, row["Endenergieverbrauch dieses Gebäudes"])
    fill_placeholder(df, 14, row["Primärenergieverbrauch dieses Gebäudes"])

    for i, rowrow in enumerate(row["Verbrauchserfassung"]):
      if rowrow["Energieverbrauch [kWh]"] == "":
        break
      fill_placeholder(df, 15, row["Endenergieverbrauch dieses Gebäudes [Pflichtangabe für Immobilienanzeigen]"], 2*i)
      fill_placeholder(df, 16, rowrow["Abrechnungszeitraum (bis)"], 2*i)
      fill_placeholder(df, 17, rowrow["Abrechnungszeitraum (von)"], 2*i)
      fill_placeholder(df, 18, rowrow["Primärenergieverbrauch [kWh/m²]"], 2*i)
      fill_placeholder(df, 19, rowrow["Energieverbrauch [kWh]"], 2*i)
      fill_placeholder(df, 20, rowrow["Anteil Warmwasser [kWh]"], 2*i)
      fill_placeholder(df, 21, rowrow["Anteil Heizung [kWh]"], 2*i)
      fill_placeholder(df, 22, rowrow["Klimafaktor"], 2*i)
      fill_placeholder(df, 23, rowrow["Kennwert [kWh/m²]"], 2*i)

    fill_placeholder(df, 24, row["Möglichkeit zur Verbesserung der Energieeffizienz"])

    for i, rowrow in enumerate(row["Empfehlungen zur kostengünstigen Modernisierung"]):
      if rowrow["Nr. Bau- oder Anlagenteile"] == "":
        break

      fill_placeholder(df, 25, rowrow["Nr. Bau- oder Anlagenteile"], i)
      fill_placeholder(df, 26, rowrow["Maßnahmenbeschreibung in einzelnen Schritten"], i)
      fill_placeholder(df, 27, rowrow["größerer Modernisierung"], i)
      fill_placeholder(df, 28, rowrow["Einzelmaßnahme"], i)

    fill_empty(df)

  elif len(pages) == 1:
    fill_placeholder(df, 13, row["Endenergieverbrauch dieses Gebäudes"])
    fill_placeholder(df, 14, row["Primärenergieverbrauch dieses Gebäudes"])
    fill_empty(df)

  elif len(pages) == 5:
    fill_placeholder(df, 39, row["Baujahr Wärmeerzeuger"])

    fill_placeholder(df, 29, row["CO2-Emissionen"])
    fill_placeholder(df, 30, row["Primärenergiebedarf (Ist-Wert)"])
    fill_placeholder(df, 31, row["Primärenergiebedarf (Anforderungswert)"])
    fill_placeholder(df, 32, row["Energetische Qualität der Gebäudehülle HT (Ist-Wert)"])
    fill_placeholder(df, 33, row["Energetische Qualität der Gebäudehülle HT (Anforderungswert)"])
    fill_placeholder(df, 34, row["Sommerlicher Wärmeschutz (bei Neubau)"])
    fill_placeholder(df, 35, row["Verfahren nach DIN V 4108-6 und DIN V 4701-10"])
    fill_placeholder(df, 36, row["Verfahren nach DIN V 18599"])
    fill_placeholder(df, 37, row["Regelung nach § 3 Absatz 5 EnEV"])
    fill_placeholder(df, 38, row["Vereinfachungen nach § 9 Abs. 2 EnEV"])

    fill_placeholder(df, 40, row["Endenergiebedarf dieses Gebäudes"])
    fill_placeholder(df, 41, row["Primärenergiebedarf dieses Gebäudes"])

    for i, rowrow in enumerate(row["Verbrauchserfassung"]):
      if rowrow["Energieverbrauch [kWh]"] == "":
        break
      fill_placeholder(df, 15, row["Endenergieverbrauch dieses Gebäudes [Pflichtangabe für Immobilienanzeigen]"], 2*i)
      fill_placeholder(df, 16, rowrow["Abrechnungszeitraum (bis)"], 2*i)
      fill_placeholder(df, 17, rowrow["Abrechnungszeitraum (von)"], 2*i)
      fill_placeholder(df, 18, rowrow["Primärenergieverbrauch [kWh/m²]"], 2*i)
      fill_placeholder(df, 19, rowrow["Energieverbrauch [kWh]"], 2*i)
      fill_placeholder(df, 20, rowrow["Anteil Warmwasser [kWh]"], 2*i)
      fill_placeholder(df, 21, rowrow["Anteil Heizung [kWh]"], 2*i)
      fill_placeholder(df, 22, rowrow["Klimafaktor"], 2*i)
      fill_placeholder(df, 23, rowrow["Kennwert [kWh/m²]"], 2*i)

    fill_placeholder(df, 24, row["Möglichkeit zur Verbesserung der Energieeffizienz"])

    for i, rowrow in enumerate(row["Empfehlungen zur kostengünstigen Modernisierung"]):
      if rowrow["Bau- oder Anlagenteile"] == "":
        break

      fill_placeholder(df, 25, rowrow["Bau- oder Anlagenteile"], i)
      fill_placeholder(df, 26, rowrow["Maßnahmenbeschreibung in einzelnen Schritten"], i)
      fill_placeholder(df, 27, rowrow["in Zusammenhang mit größerer Modernisierung"], i)
      fill_placeholder(df, 28, rowrow["als Einzelmaßnahme"], i)

    fill_empty(df)

  df_all = pd.concat([df_all, df])


now = datetime.now()
ftime = now.strftime("%m%d%Y_%H%M%S")

columns = df_all.columns
first_row = df_all.iloc[:1 , :]
df_except_first_row = df_all.iloc[1: , :]
df_except_first_row = df_except_first_row[df_except_first_row[columns[0]] != "Filename"]
df_all = pd.concat([first_row, df_except_first_row])
df_all.to_excel(f"output/{ftime}.xlsx", sheet_name="Sheet1", header=False, index=False)

print("Done!")
