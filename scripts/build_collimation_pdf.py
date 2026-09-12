#!/usr/bin/env python3
"""
scripts/build_collimation_pdf.py - Compiles a publication-quality, printable
PDF tutorial on Dobsonian mirror collimation (Sky-Watcher Skyliner 200P).
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
PYLIBS_DIR = os.path.join(REPO_ROOT, '.pylibs')
if PYLIBS_DIR not in sys.path:
    sys.path.insert(0, PYLIBS_DIR)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor('#64748b'))

        # Header rule & title (Pages 2+)
        if self._pageNumber > 1:
            self.setLineWidth(0.5)
            self.setStrokeColor(colors.HexColor('#cbd5e1'))
            self.line(18*mm, 282*mm, 192*mm, 282*mm)
            self.drawString(18*mm, 284*mm, "SKY-WATCHER 200P DOBSONIAN — MIRROR COLLIMATION GUIDE")

        # Footer
        self.setLineWidth(0.5)
        self.setStrokeColor(colors.HexColor('#cbd5e1'))
        self.line(18*mm, 15*mm, 192*mm, 15*mm)
        self.drawString(18*mm, 10.5*mm, "Stargazing Field Manual  •  Optical Collimation Tutorial  •  Sky-Watcher Skyliner Classic 200P (f/6)")
        self.drawRightString(192*mm, 10.5*mm, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf():
    tutorials_dir = os.path.join(REPO_ROOT, 'tutorials')
    img_dir = os.path.join(tutorials_dir, 'images')
    pdf_path = os.path.join(tutorials_dir, 'dobsonian-mirror-collimation.pdf')

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=18*mm,
        rightMargin=18*mm,
        topMargin=15*mm,
        bottomMargin=18*mm
    )

    styles = getSampleStyleSheet()

    c_dark = colors.HexColor('#0f172a')
    c_blue = colors.HexColor('#0284c7')
    c_navy = colors.HexColor('#1e3a8a')
    c_sub = colors.HexColor('#475569')

    title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=15, leading=18, textColor=c_navy, spaceAfter=3)
    subtitle_style = ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12.5, textColor=c_sub, spaceAfter=8)
    h1_style = ParagraphStyle('Heading1_Custom', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=c_navy, spaceBefore=6, spaceAfter=4, keepWithNext=True)
    body_style = ParagraphStyle('Body_Custom', parent=styles['Normal'], fontName='Helvetica', fontSize=8.0, leading=11.0, textColor=c_dark, spaceAfter=4)
    body_bold = ParagraphStyle('Body_Bold', parent=body_style, fontName='Helvetica-Bold')
    callout_style = ParagraphStyle('Callout_Text', parent=styles['Normal'], fontName='Helvetica', fontSize=7.8, leading=10.8, textColor=colors.HexColor('#1e293b'))
    table_hdr = ParagraphStyle('TableHdr', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.8, leading=9.5, textColor=colors.white, alignment=1)
    table_cell = ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=7.4, leading=9.5, textColor=c_dark)
    table_cell_style = table_cell
    table_cell_bold = ParagraphStyle('TableCellBold', parent=table_cell, fontName='Helvetica-Bold')
    table_cell_center = ParagraphStyle('TableCellCenter', parent=table_cell, alignment=1)

    story = []

    # =========================================================================
    # PAGE 1: OVERVIEW, SAFETY & HARDWARE CONTROLS
    # =========================================================================
    story.append(Paragraph("NEWTONIAN DOBSONIAN MIRROR COLLIMATION GUIDE", title_style))
    story.append(Paragraph("<b>Instrument:</b> Sky-Watcher Skyliner Classic 200P (200 mm / 8\" f/6 Newtonian Reflector, 1200 mm FL)<br/>"
                           "<b>Purpose:</b> Complete visual guide for secondary and primary mirror alignment and high-power star testing.", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_blue, spaceAfter=8))

    # Critical Safety Callout Banner
    safety_data = [[
        Paragraph("<b>CRITICAL SAFETY PROTOCOL: ORIENT TUBE HORIZONTALLY BEFORE COLLIMATING!</b><br/>"
                  "<b>1. Never collimate with the optical tube pointing straight up!</b> If an Allen key, screwdriver, or thumbscrew slips from your fingers, it will fall directly onto the 200 mm primary mirror and shatter or chip the optical coatings.<br/>"
                  "<b>2. Position the tube horizontally or tilted 20°–30° above the ground.</b> Any dropped tool will simply hit the steel tube wall.<br/>"
                  "<b>3. Never overtighten screws:</b> Firm finger tightness is sufficient. Excessive torque on mirror clips or locking screws creates optical astigmatism (pinched optics).", callout_style)
    ]]
    t_safety = Table(safety_data, colWidths=[174*mm])
    t_safety.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fef2f2')),
        ('BOX', (0,0), (-1,-1), 1.2, colors.HexColor('#ef4444')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(t_safety)
    story.append(Spacer(1, 6))

    # Two-column box: Optical Theory vs Recommended Tools
    box_data = [
        [
            Paragraph("<b>OPTICAL ALIGNMENT FUNDAMENTALS</b><br/>"
                      "A Newtonian reflector requires two optical axes to be coincident:<br/>"
                      "• <b>Optical Axis:</b> The parabolic axis of the primary mirror.<br/>"
                      "• <b>Focuser Axis:</b> The mechanical centerline of the eyepiece drawtube.<br/>"
                      "• <b>Secondary Flat (Diagonal):</b> Must sit centered under the drawtube and angled at precisely 45° to fold the cone into the eyepiece.<br/>"
                      "At f/6, the collimation tolerance is moderate (coma-free sweet spot is ~2.8 mm across), but precise alignment is essential to resolve tight double stars, globular cores, and planetary rings.", body_style),
            Paragraph("<b>RECOMMENDED COLLIMATION TOOLS</b><br/>"
                      "• <b>Collimation Cap:</b> Plastic cap with a 1-2 mm central peephole and reflective interior underside. Simple, robust, immune to tool miscalibration.<br/>"
                      "• <b>Cheshire Eyepiece / Sight Tube:</b> Long barrel with crosshairs and 45° reflective cutout. Best tool for both secondary and primary alignment.<br/>"
                      "• <b>Laser Collimator:</b> Convenient at night, but only reliable if the laser itself is precisely collimated in a V-block first!<br/>"
                      "• <b>High-Power Eyepiece:</b> 12.5 mm or Barlowed eyepiece for the final optical star test on Polaris.", body_style)
        ]
    ]
    t_box = Table(box_data, colWidths=[85*mm, 85*mm])
    t_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1.0, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_box)
    story.append(Spacer(1, 6))

    # Hardware Controls Diagram
    story.append(Paragraph("<b>MECHANICAL HARDWARE CONTROLS ON THE SKY-WATCHER 200P</b>", h1_style))
    hw_img = os.path.join(img_dir, 'collimation_hardware_controls.png')
    story.append(Image(hw_img, width=174*mm, height=72*mm))
    story.append(Spacer(1, 4))

    # Hardware Summary Table
    hw_table_data = [
        [Paragraph("Control Component", table_hdr), Paragraph("Location & Tool", table_hdr), Paragraph("Action & Directional Effect", table_hdr), Paragraph("Operational Rule", table_hdr)],
        [Paragraph("<b>Center Hub Bolt</b>", table_cell_bold), Paragraph("Spider Hub (Phillips/Slotted)", table_cell_style), Paragraph("Moves secondary mirror in/out along optical tube axis.", table_cell_style), Paragraph("Loosen 3 tilt screws slightly before adjusting. Hold holder!", table_cell_style)],
        [Paragraph("<b>3× Secondary Tilt Screws</b>", table_cell_bold), Paragraph("Spider Hub (2.0 or 2.5 mm Allen)", table_cell_style), Paragraph("Tilts diagonal flat toward the primary mirror center donut.", table_cell_style), Paragraph("Adjust in tiny 1/8-turn increments. As one tightens, loosen others.", table_cell_style)],
        [Paragraph("<b>3× Primary Collimation Thumbscrews</b>", table_cell_bold), Paragraph("Rear Cell (Large White/Silver)", table_cell_style), Paragraph("Tilts primary mirror by compressing heavy internal springs.", table_cell_style), Paragraph("Moves tool reflection into concentricity with the donut.", table_cell_style)],
        [Paragraph("<b>3× Primary Locking Screws</b>", table_cell_bold), Paragraph("Rear Cell (Small Black Screws)", table_cell_style), Paragraph("Locks primary mirror cell in place to prevent drift.", table_cell_style), Paragraph("MUST be loosened 1/2 turn before collimating! Snug gently after.", table_cell_style)],
    ]
    t_hw = Table(hw_table_data, colWidths=[40*mm, 42*mm, 52*mm, 40*mm])
    t_hw.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_hw)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: THE 3-STEP SIGHT TUBE / CHESHIRE PROCEDURE
    # =========================================================================
    story.append(Paragraph("THE 3-STEP COLLIMATION PROCEDURE (SIGHT TUBE / CHESHIRE VIEW)", h1_style))
    story.append(Paragraph("Look straight down the focuser drawtube with a Cheshire eyepiece or Collimation Cap. Follow these three steps in strict sequence:", body_style))

    # Sight tube views progression diagram
    views_img = os.path.join(img_dir, 'collimation_steps_view.png')
    story.append(Image(views_img, width=174*mm, height=48*mm))
    story.append(Spacer(1, 6))

    # Step-by-Step Instructions Table
    steps_data = [
        [
            Paragraph("<b>STEP 1: CENTER SECONDARY UNDER FOCUSER (Panel B)</b><br/>"
                      "<b>Goal:</b> Make the secondary mirror appear circular and centered under the focuser drawtube.<br/>"
                      "1. Rack the focuser all the way in, then slowly rack outward while looking through the collimation cap peephole until the rim of the secondary mirror is just slightly smaller than the inside barrel of the drawtube.<br/>"
                      "2. <i>Position Error (Left/Right):</i> Loosen the 3 Allen tilt screws slightly and turn the large center Phillips bolt to slide the secondary holder along the tube until centered.<br/>"
                      "3. <i>Rotation Error (Oval shape):</i> Rotate the secondary holder by hand until the face points directly square at the focuser tube (it looks like a true circle, not an egg). Lightly tighten the 3 screws.", body_style),
            Paragraph("<b>STEP 2: ALIGN SECONDARY TILT (Panel C)</b><br/>"
                      "<b>Goal:</b> Aim the secondary mirror so its crosshairs point directly at the primary mirror donut.<br/>"
                      "1. Look through the sight tube / Cheshire crosshairs.<br/>"
                      "2. You should see the bright reflection of the primary mirror. Confirm you can see <b>all three mirror clips</b> evenly spaced around the edge.<br/>"
                      "3. Insert a 2.0 or 2.5 mm Allen key into the 3 spider hub tilt screws.<br/>"
                      "4. Adjust the screws in tiny fractional turns (tightening one while loosening the opposite two) until the <b>crosshairs intersect dead-center inside the primary mirror center donut ring</b>.", body_style)
        ],
        [
            Paragraph("<b>STEP 3: ALIGN PRIMARY MIRROR TILT (Panel D)</b><br/>"
                      "<b>Goal:</b> Tilt the primary mirror so the reflection of the collimation tool pupil is concentric with the donut.<br/>"
                      "1. Move to the rear of the telescope tube.<br/>"
                      "2. <b>Loosen the 3 small black locking thumbscrews</b> by 1/2 turn counter-clockwise.<br/>"
                      "3. Look into the Cheshire / Collimation cap. Locate the dark center spot (the reflection of your eye / collimation cap pupil).<br/>"
                      "4. Slowly turn the <b>3 large white/silver collimation thumbscrews</b> one at a time while observing the motion of the black spot.<br/>"
                      "5. Adjust until the <b>black spot sits perfectly centered inside the red/white primary donut ring</b>.<br/>"
                      "6. Gently snug the 3 black locking thumbscrews. Re-check the view—if tightening shifted the spot, counter-adjust slightly.", body_style),
            Paragraph("<b>VERIFICATION CHECKLIST (PANEL D: FULL CONCENTRICITY)</b><br/>"
                      "When your Newtonian reflector is fully collimated, everything will appear concentric like a bullseye:<br/>"
                      "1. Outer circle: Focuser drawtube barrel.<br/>"
                      "2. Second circle: Outer rim of secondary mirror.<br/>"
                      "3. Third circle: Reflection of primary mirror with all 3 support clips visible at 120° intervals.<br/>"
                      "4. Inner circle: Primary mirror center marker donut.<br/>"
                      "5. Core dot: Reflection of observer's pupil / collimation cap peephole.<br/>"
                      "<i>Notice: The silhouette reflection of the secondary mirror holder will appear slightly offset toward the primary mirror—this is normal optical offset in fast Newtonians!</i>", body_style)
        ]
    ]
    t_steps = Table(steps_data, colWidths=[85*mm, 85*mm])
    t_steps.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1.0, colors.HexColor('#cbd5e1')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_steps)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: FIELD STAR TEST & TROUBLESHOOTING
    # =========================================================================
    story.append(Paragraph("FIELD STAR TEST & DIAGNOSTIC TROUBLESHOOTING", h1_style))
    story.append(Paragraph("The artificial collimation tools get you 95% of the way. The optical star test on a real night sky star is the definitive, ultimate verification of optical wavefront alignment.", body_style))

    # Star test patterns diagram
    star_img = os.path.join(img_dir, 'star_test_patterns.png')
    story.append(Image(star_img, width=174*mm, height=84*mm))
    story.append(Spacer(1, 5))

    # Star Test Procedure
    story.append(Paragraph("<b>HOW TO CONDUCT THE STAR TEST AT THE EYEPIECE</b>", h1_style))
    star_proc_data = [
        [
            Paragraph("<b>1. Acclimate Optics:</b> Ensure the 200 mm primary mirror has cooled outdoors for at least 30–45 minutes.<br/>"
                      "<b>2. Choose Target Star:</b> Pick a 2nd–3rd magnitude star high in the sky (e.g. Polaris, which stays fixed and doesn't drift!).<br/>"
                      "<b>3. High Magnification:</b> Insert your 12.5 mm eyepiece (96×) or add a 2× Barlow (192×). Center the star dead-center in the field of view (Newtonian off-axis coma will mimic miscollimation if the star is near the field edge!).<br/>"
                      "<b>4. Defocus Slightly:</b> Turn the focuser knob just 1/4 to 1/2 turn inside and outside of focus. Observe the circular diffraction rings and central dark secondary shadow.", body_style)
        ]
    ]
    t_star_proc = Table(star_proc_data, colWidths=[174*mm])
    t_star_proc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
        ('BOX', (0,0), (-1,-1), 1.0, colors.HexColor('#94a3b8')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_star_proc)
    story.append(Spacer(1, 5))

    # Troubleshooting & Diagnostics Table
    trouble_data = [
        [Paragraph("Observed Pattern / Symptom", table_hdr), Paragraph("Root Optical Cause", table_hdr), Paragraph("Corrective Field Action", table_hdr)],
        [Paragraph("<b>Decentered Rings / Coma Flare</b><br/>Secondary shadow is shifted to one side; flared tail at focus.", table_cell_bold),
         Paragraph("Primary mirror tilt is slightly misaligned.", table_cell_style),
         Paragraph("Center star in eyepiece. Adjust rear white thumbscrews in tiny fractions until rings become perfectly concentric bullseyes.", table_cell_style)],
        [Paragraph("<b>Triangular / Trefoil Rings</b><br/>Diffraction rings show 3 distinct lobes / corners.", table_cell_bold),
         Paragraph("Pinched optics: Primary mirror support clips are screwed down too tightly against the glass.", table_cell_style),
         Paragraph("Loosen the primary mirror retaining clip screws until a business card can slip freely between the rubber clip and the mirror face.", table_cell_style)],
        [Paragraph("<b>Astigmatic Ellipse Flip</b><br/>Star elongates into an ellipse that flips 90° when racking through focus.", table_cell_bold),
         Paragraph("Secondary mirror holder glued unevenly, or diagonal stalk overtightened.", table_cell_style),
         Paragraph("Loosen secondary center bolt and 3 Allen screws; verify holder is not clamped under mechanical stress.", table_cell_style)],
        [Paragraph("<b>Boiling / Shimmering Rings</b><br/>Diffraction pattern is turbulent; rings constantly morphing.", table_cell_bold),
         Paragraph("Thermal boundary layer on primary mirror or turbulent atmospheric seeing.", table_cell_style),
         Paragraph("Wait another 20–30 minutes for mirror cooldown. Run rear cooling fan. Pick a night with calmer upper-air seeing.", table_cell_style)],
        [Paragraph("<b>Collimation Shifts During Slew</b><br/>Collimation changes when pointing from zenith to low horizon.", table_cell_bold),
         Paragraph("Loose spider vanes or weak primary mirror spring tension.", table_cell_style),
         Paragraph("Tighten 4 spider vane knurled nuts on outside of tube. Tighten all 3 primary thumbscrews clockwise halfway to compress springs.", table_cell_style)],
    ]
    t_trouble = Table(trouble_data, colWidths=[52*mm, 54*mm, 68*mm])
    t_trouble.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_trouble)
    story.append(Spacer(1, 4))

    # Video Tutorials Callout Box
    video_data = [
        [
            Paragraph("<b>RECOMMENDED VIDEO TUTORIALS (LIVE EYEPIECE FOOTAGE & DEMONSTRATIONS)</b><br/>"
                      "• <b>Star Test to Fix Your Telescope (AstroBiscuits):</b> Live footage filmed directly through telescope eyepieces showing real defocused diffraction rings, coma tail flaring, and star adjustments: <u>https://www.youtube.com/watch?v=mviFGu37AcI</u><br/>"
                      "• <b>How to Collimate your Dobsonian (Small Optics):</b> Complete hands-on tutorial using a Sky-Watcher Dobsonian, demonstrating secondary rotation and rear primary screws: <u>https://www.youtube.com/watch?v=ht0WAEpya1o</u><br/>"
                      "• <b>How to Collimate a Telescope (Orion Telescopes):</b> Optical ray animations and alignment tool mechanics: <u>https://www.youtube.com/watch?v=YAVGcGEBmCE</u>", callout_style)
        ]
    ]
    t_video = Table(video_data, colWidths=[174*mm])
    t_video.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
        ('BOX', (0,0), (-1,-1), 1.0, colors.HexColor('#3b82f6')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_video)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Collimation Guide PDF successfully built: {pdf_path}")

if __name__ == '__main__':
    build_pdf()
