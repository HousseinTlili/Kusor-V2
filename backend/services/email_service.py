"""
KUSOR v3 — Institutional Email & Alert Service
Sends certified regulatory alerts, KYC risk notices, and weekly digests via Gmail SMTP.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "bynour70@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "lpqzqittrwxihyzv")
DEFAULT_RECIPIENT = os.getenv("ALERT_EMAIL_RECIPIENT", "bynour70@gmail.com")


def send_regulatory_email(
    subject: str,
    html_content: str,
    to_email: Optional[str] = None,
    sender_name: str = "KUSOR — Conformité Attijari Bank"
) -> Dict[str, Any]:
    """
    Send an HTML email via secure SSL Gmail SMTP.
    """
    recipient = to_email or DEFAULT_RECIPIENT
    sender = SMTP_USER
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender}>"
    msg["To"] = recipient
    
    msg.attach(MIMEText(html_content, "html"))
    
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(sender, SMTP_PASSWORD)
            server.sendmail(sender, recipient, msg.as_string())
        return {
            "success": True,
            "recipient": recipient,
            "subject": subject
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def send_impact_alert(circular_number: str, severity: str, summary: str, affected_count: int = 1) -> Dict[str, Any]:
    """Sends a high-priority red alert email for critical regulatory changes."""
    subject = f"🚨 ALERTE CONFORMITÉ CRITIQUE — Nouvelle Circulaire BCT N° {circular_number}"
    
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 650px; margin: 0 auto; background-color: #0A0A0A; color: #F1F5F9; border-radius: 16px; border: 1px solid rgba(244, 63, 94, 0.4); overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
      <div style="background: linear-gradient(135deg, #4C0519 0%, #1E0007 100%); padding: 30px 25px; border-bottom: 2px solid #F43F5E; text-align: center;">
        <div style="font-size: 11px; font-weight: 800; color: #F43F5E; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 6px;">Alerte Immédiate de Propagation des Risques</div>
        <h1 style="margin: 0; font-size: 22px; font-weight: 900; color: #FFFFFF;">🚨 Alerte de Conformité : Impact Réglementaire Détecté</h1>
        <p style="margin: 6px 0 0 0; font-size: 13px; color: #FDA4AF;">Circulaire BCT N° {circular_number}</p>
      </div>
      <div style="padding: 25px;">
        <div style="background-color: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.3); border-radius: 12px; padding: 15px; margin-bottom: 20px; text-align: center;">
          <span style="font-size: 11px; font-weight: 800; text-transform: uppercase; color: #94A3B8;">Niveau de Sévérité :</span>
          <span style="font-size: 14px; font-weight: 900; color: #F43F5E; margin-left: 8px; padding: 4px 10px; background-color: rgba(244, 63, 94, 0.2); border-radius: 6px;">{severity}</span>
        </div>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px;">
          <tr style="border-bottom: 1px solid #1E293B;">
            <td style="padding: 10px 0; color: #94A3B8; font-weight: 700; width: 40%;">Circulaire Source :</td>
            <td style="padding: 10px 0; color: #FFFFFF; font-weight: 800;">Circulaire BCT N° {circular_number}</td>
          </tr>
          <tr style="border-bottom: 1px solid #1E293B;">
            <td style="padding: 10px 0; color: #94A3B8; font-weight: 700;">Processus / Contrats Impactés :</td>
            <td style="padding: 10px 0; color: #F59E0B; font-weight: 800;">{affected_count} élément(s) affecté(s)</td>
          </tr>
        </table>
        <div style="background-color: #03071E; border: 1px solid #1E293B; border-radius: 12px; padding: 18px; margin: 20px 0;">
          <div style="font-size: 11px; font-weight: 800; color: #F43F5E; text-transform: uppercase; margin-bottom: 6px;">Description de l'Impact :</div>
          <p style="font-size: 13px; line-height: 1.6; color: #E2E8F0; margin: 0;">{summary}</p>
        </div>
        <div style="text-align: center; margin: 25px 0 10px 0;">
          <a href="http://localhost:5000/impact-viewer" style="background: linear-gradient(135deg, #E11D48 0%, #BE123C 100%); color: #FFFFFF; text-decoration: none; padding: 12px 28px; font-weight: 800; font-size: 13px; border-radius: 10px; display: inline-block;">
            Visualiser l'Arbre d'Impact (Graph Viewer) →
          </a>
        </div>
      </div>
      <div style="background-color: #03071E; padding: 15px 25px; border-top: 1px solid #1E293B; font-size: 11px; color: #64748B; text-align: center;">
        Notification émise par KUSOR v3 • Direction de la Conformité Attijari Bank Tunisia
      </div>
    </div>
    """
    return send_regulatory_email(subject=subject, html_content=html)
