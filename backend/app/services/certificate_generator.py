import io
import os
import qrcode
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

class DigitalCertificateGenerator:
    """
    Generator Sertifikat Mutu Digital TBS Resmi (PDF)
    Sesuai Pedoman Mutu Pabrik Kelapa Sawit (IOPRI 1997) dan Kepatuhan EUDR 2023/1115.
    """

    @classmethod
    def generate_pdf(cls, session_data: dict, farmer_data: dict, block_data: dict, order_data: dict) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography Styles
        title_style = ParagraphStyle(
            "CertTitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            alignment=1,  # Center
            textColor=colors.HexColor("#064e3b"),
            fontName="Helvetica-Bold"
        )
        subtitle_style = ParagraphStyle(
            "CertSubTitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            alignment=1,
            textColor=colors.HexColor("#4b5563")
        )
        section_style = ParagraphStyle(
            "CertSection",
            parent=styles["Heading2"],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#0f766e"),
            fontName="Helvetica-Bold",
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            "CertBody",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#1f2937")
        )
        body_bold = ParagraphStyle(
            "CertBodyBold",
            parent=body_style,
            fontName="Helvetica-Bold"
        )

        elements = []

        # --- 1. Header Kop Resmi Institusi ---
        header_text = [
            Paragraph("<b>SMART GRADE - SISTEM INSPEKSI MUTU DIGITAL TBS SAWIT</b>", title_style),
            Paragraph("Politeknik Citra Widya Edukasi (PCWE) & Pusat Penelitian Kelapa Sawit (PPKS)", subtitle_style),
            Paragraph("Sertifikat Verifikasi Mutu TBS, Estimasi OER & Ketertelusuran EUDR/ISPO", subtitle_style),
            Spacer(1, 0.4 * cm)
        ]
        elements.extend(header_text)

        # Garis Pembatas Kop
        divider = Table([[""]], colWidths=[18 * cm], rowHeights=[2])
        divider.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#059669")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(divider)
        elements.append(Spacer(1, 0.4 * cm))

        # --- 2. Generate QR Code Verifikasi Keaslian ---
        session_code = session_data.get("session_code", "GRD-UNKNOWN")
        verify_url = f"https://smartgrade.pcwe.ac.id/verify/{session_code}"
        
        qr = qrcode.QRCode(version=1, box_size=4, border=1)
        qr.add_data(verify_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#064e3b", back_color="white")
        
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        qr_element = RLImage(qr_buffer, width=2.8 * cm, height=2.8 * cm)

        # Informasi Dokumen dan QR
        now_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S WIB")
        cert_meta = [
            [
                Paragraph("<b>Nomor Sertifikat:</b>", body_style),
                Paragraph(f"<b>{session_code}</b>", body_bold),
                qr_element
            ],
            [
                Paragraph("<b>Tanggal & Jam Uji:</b>", body_style),
                Paragraph(session_data.get("graded_at", now_str), body_style),
                ""
            ],
            [
                Paragraph("<b>Petugas / Operator:</b>", body_style),
                Paragraph(session_data.get("operator_name", "Petugas Grader PKS"), body_style),
                ""
            ],
            [
                Paragraph("<b>Model & Versi AI:</b>", body_style),
                Paragraph(f"{session_data.get('model_version', 'YOLOv8-IOPRI')} (ONNX Edge)", body_style),
                ""
            ]
        ]
        t_meta = Table(cert_meta, colWidths=[4 * cm, 10.5 * cm, 3.5 * cm])
        t_meta.setStyle(TableStyle([
            ("SPAN", (2, 0), (2, 3)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(t_meta)
        elements.append(Spacer(1, 0.4 * cm))

        # --- 3. Informasi Asal Kebun & Ketertelusuran EUDR ---
        elements.append(Paragraph("I. DATA IDENTITAS PEKEBUN & KEPATUHAN SPASIAL (EUDR/ISPO)", section_style))
        
        eudr_status = block_data.get("eudr_compliant", "VERIFIED")
        eudr_color = "#047857" if eudr_status == "VERIFIED" else "#b91c1c"
        
        trace_table_data = [
            [
                Paragraph("<b>Nama Pekebun / Koperasi:</b>", body_style),
                Paragraph(farmer_data.get("name", "-"), body_bold),
                Paragraph("<b>No. SPB / DO:</b>", body_style),
                Paragraph(order_data.get("spb_number", "-"), body_bold),
            ],
            [
                Paragraph("<b>Kode Pekebun (STDB):</b>", body_style),
                Paragraph(farmer_data.get("farmer_code", "-"), body_style),
                Paragraph("<b>No. Plat Truk:</b>", body_style),
                Paragraph(order_data.get("truck_plate_number", "-"), body_style),
            ],
            [
                Paragraph("<b>Status Sertifikasi:</b>", body_style),
                Paragraph(farmer_data.get("certification_status", "ISPO"), body_style),
                Paragraph("<b>Bobot Netto Pengiriman:</b>", body_style),
                Paragraph(f"{order_data.get('net_weight_kg', 0):,.1f} Kg", body_bold),
            ],
            [
                Paragraph("<b>Blok Kebun & Legalitas:</b>", body_style),
                Paragraph(f"{block_data.get('block_code', '-')} ({block_data.get('legal_status', 'SHM')})", body_style),
                Paragraph("<b>Koordinat Titik Acuan:</b>", body_style),
                Paragraph(f"{block_data.get('latitude', 0.0):.4f}, {block_data.get('longitude', 0.0):.4f}", body_style),
            ],
            [
                Paragraph("<b>Luas Kebun / Varietas:</b>", body_style),
                Paragraph(f"{block_data.get('area_hectares', 1.0)} Ha | {block_data.get('variety', 'DxP')}", body_style),
                Paragraph("<b>Verifikasi EUDR (2023/1115):</b>", body_style),
                Paragraph(f"<font color='{eudr_color}'><b>{eudr_status} (Cut-off Dec 2020 Clean)</b></font>", body_bold),
            ]
        ]
        t_trace = Table(trace_table_data, colWidths=[4.2 * cm, 4.8 * cm, 4.2 * cm, 4.8 * cm])
        t_trace.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t_trace)
        elements.append(Spacer(1, 0.4 * cm))

        # --- 4. Rincian Deteksi Fraksi Kematangan & Tangkai ---
        elements.append(Paragraph("II. HASIL INSPEKSI MUTU & SEBARAN FRAKSI TBS (STANDAR PPKS/IOPRI)", section_style))
        
        assessment = session_data.get("assessment", {})
        total_bunches = assessment.get("total_bunches", session_data.get("total_bunches", 0))
        
        grading_table_data = [
            [
                Paragraph("<b>Kategori Fraksi / Cacat</b>", body_bold),
                Paragraph("<b>Kriteria Mutu</b>", body_bold),
                Paragraph("<b>Jumlah (Tandan)</b>", body_bold),
                Paragraph("<b>Persentase (%)</b>", body_bold),
                Paragraph("<b>Status Toleransi</b>", body_bold),
            ],
            [
                Paragraph("Fraksi 2-3: Matang (Ripe)", body_style),
                Paragraph("Brondol lepas > 10 buah", body_style),
                Paragraph(str(assessment.get("ripe_count", 0)), body_style),
                Paragraph(f"{assessment.get('ripe_percentage', 0.0):.1f}%", body_style),
                Paragraph("<font color='#059669'><b>Optimal</b></font>", body_style),
            ],
            [
                Paragraph("Fraksi 1: Kurang Masak (Underripe)", body_style),
                Paragraph("Brondol lepas 1-9 buah", body_style),
                Paragraph(str(assessment.get("underripe_count", 0)), body_style),
                Paragraph(f"{assessment.get('underripe_percentage', 0.0):.1f}%", body_style),
                Paragraph("Toleransi maks. 5%", body_style),
            ],
            [
                Paragraph("Fraksi 0: Mentah (Unripe)", body_style),
                Paragraph("0 brondolan lepas", body_style),
                Paragraph(str(assessment.get("unripe_count", 0)), body_style),
                Paragraph(f"{assessment.get('unripe_percentage', 0.0):.1f}%", body_style),
                Paragraph("<font color='#dc2626'><b>Penalti (Toleransi 0%)</b></font>", body_style),
            ],
            [
                Paragraph("Fraksi 4-5: Terlalu Masak (Overripe)", body_style),
                Paragraph("Buah membusuk / lepas > 50%", body_style),
                Paragraph(str(assessment.get("overripe_count", 0)), body_style),
                Paragraph(f"{assessment.get('overripe_percentage', 0.0):.1f}%", body_style),
                Paragraph("Toleransi maks. 10%", body_style),
            ],
            [
                Paragraph("Tangkai Panjang (> 2.5 cm)", body_style),
                Paragraph("Gagang buah belum dipotong mepet", body_style),
                Paragraph(str(assessment.get("long_stalk_count", 0)), body_style),
                Paragraph(f"{assessment.get('long_stalk_percentage', 0.0):.1f}%", body_style),
                Paragraph("Potongan bobot kotor", body_style),
            ],
            [
                Paragraph("<b>TOTAL SAMPEL GRADED</b>", body_bold),
                Paragraph("<b>-</b>", body_style),
                Paragraph(f"<b>{total_bunches} Tandan</b>", body_bold),
                Paragraph("<b>100.0%</b>", body_bold),
                Paragraph("<b>-</b>", body_style),
            ]
        ]
        t_grade = Table(grading_table_data, colWidths=[5 * cm, 4.5 * cm, 2.8 * cm, 2.7 * cm, 3 * cm])
        t_grade.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ALIGN", (2, 0), (3, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t_grade)
        elements.append(Spacer(1, 0.4 * cm))

        # --- 5. Ringkasan OER & Penetapan Harga Beli Bersih ---
        elements.append(Paragraph("III. ESTIMASI OER PKS & PENETAPAN HARGA BELI ADIL (FAIR SETTLEMENT)", section_style))
        
        oer_val = assessment.get("estimated_oer_percentage", 21.5)
        base_price = assessment.get("price_per_kg_base", 2850.0)
        final_price = assessment.get("final_price_per_kg", 2850.0)
        price_penalty = assessment.get("price_penalty_percentage", 0.0)
        stalk_penalty = assessment.get("stalk_penalty_percentage", 0.0)
        eff_weight = assessment.get("effective_net_weight_kg", order_data.get("net_weight_kg", 0.0))
        total_payout = assessment.get("total_payout", 0.0)
        ffa_risk = assessment.get("ffa_risk_category", "LOW")

        settlement_data = [
            [
                Paragraph("<b>Estimasi Rendemen Minyak (OER):</b>", body_style),
                Paragraph(f"<b>{oer_val:.2f}%</b> (Benchmark: 21.50%)", body_bold),
                Paragraph("<b>Kategori Risiko ALB (FFA):</b>", body_style),
                Paragraph(f"<b>{ffa_risk}</b>", body_bold),
            ],
            [
                Paragraph("<b>Harga Acuan TBS Penetapan:</b>", body_style),
                Paragraph(f"Rp {base_price:,.2f} / Kg", body_style),
                Paragraph("<b>Potongan Mutu Fraksi:</b>", body_style),
                Paragraph(f"-{price_penalty:.2f}%", body_style),
            ],
            [
                Paragraph("<b>Potongan Bobot Tangkai:</b>", body_style),
                Paragraph(f"-{stalk_penalty:.2f}%", body_style),
                Paragraph("<b>Harga Beli Akhir Bersih:</b>", body_style),
                Paragraph(f"<b>Rp {final_price:,.2f} / Kg</b>", body_bold),
            ],
            [
                Paragraph("<b>Bobot Bersih Efektif:</b>", body_style),
                Paragraph(f"{eff_weight:,.1f} Kg", body_style),
                Paragraph("<b>TOTAL NILAI PEMBAYARAN:</b>", body_bold),
                Paragraph(f"<font color='#065f46' size='10'><b>Rp {total_payout:,.0f}</b></font>", body_bold),
            ]
        ]
        t_settle = Table(settlement_data, colWidths=[4.8 * cm, 4.2 * cm, 4.5 * cm, 4.5 * cm])
        t_settle.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
            ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#16a34a")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbf7d0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t_settle)
        elements.append(Spacer(1, 0.5 * cm))

        # --- 6. Tanda Tangan & Disclaimer Integritas ---
        sig_data = [
            [
                Paragraph("<i>Dokumen ini diterbitkan secara otomatis oleh sistem AI SMART GRADE Politeknik Citra Widya Edukasi dan memiliki kekuatan pembuktian digital yang sah tanpa tanda tangan basah.</i>", ParagraphStyle("Disc", parent=body_style, fontSize=7, leading=9, textColor=colors.HexColor("#64748b"))),
                Paragraph("<b>PKS Penanggung Jawab,</b><br/><br/><br/><u>( Sistem Verifikasi Otomatis )</u><br/>NIP. 2026-PCWE-SMARTGRADE", ParagraphStyle("Sign", parent=body_style, alignment=1))
            ]
        ]
        t_sig = Table(sig_data, colWidths=[12.5 * cm, 5.5 * cm])
        t_sig.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(t_sig)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
