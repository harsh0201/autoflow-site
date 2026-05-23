"""
Vercel Serverless Function - Proposal Engine
POST /api/intake

Env vars (Vercel dashboard):
  GMAIL_USER, GMAIL_PASS, SENDER_NAME
  LS_STARTER, LS_GROWTH, LS_SCALE   (Lemon Squeezy checkout URLs)
  PAYPAL_ME                          (fallback if LS not set)
"""

from http.server import BaseHTTPRequestHandler
import json, os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER   = os.getenv("GMAIL_USER",   "heyautoflow02@gmail.com")
GMAIL_PASS   = os.getenv("GMAIL_PASS",   "")
SENDER_NAME  = os.getenv("SENDER_NAME",  "Harsh | AutoFlow AI")
PAYPAL_ME    = os.getenv("PAYPAL_ME",    "")
LS_STARTER   = os.getenv("LS_STARTER",   "")
LS_GROWTH    = os.getenv("LS_GROWTH",    "")
LS_SCALE     = os.getenv("LS_SCALE",     "")

PLANS = {
    "starter": {"name": "Starter", "price": "$1,500/mo", "ls": LS_STARTER},
    "growth":  {"name": "Growth",  "price": "$2,500/mo", "ls": LS_GROWTH},
    "scale":   {"name": "Scale",   "price": "$4,500/mo", "ls": LS_SCALE},
}

def payment_link(plan_key):
    ls = PLANS.get(plan_key, {}).get("ls", "")
    if ls:
        return ls
    if PAYPAL_ME:
        amt = {"starter": "1500", "growth": "2500", "scale": "4500"}.get(plan_key, "1500")
        return PAYPAL_ME + "/" + amt
    return "mailto:" + GMAIL_USER + "?subject=AutoFlow%20Onboarding"

def cta_label(plan_key):
    ls = PLANS.get(plan_key, {}).get("ls", "")
    if ls:
        return "Pay & Get Started"
    if PAYPAL_ME:
        return "Pay via PayPal"
    return "Reply to Start"

def build_proposal(data):
    name    = data.get("name", "there")
    company = data.get("company", "your agency")
    pain    = data.get("pain", "reporting and content briefs")
    plan_k  = data.get("plan", "growth").lower()
    plan    = PLANS.get(plan_k, PLANS["growth"])
    link    = payment_link(plan_k)
    label   = cta_label(plan_k)

    subject = "Your AutoFlow AI Automation Plan for " + company

    body = (
        "<html><body style='font-family:sans-serif;max-width:600px;margin:auto;color:#111'>"
        "<h2 style='color:#5b21b6'>Your Custom Automation Plan</h2>"
        "<p>Hey " + name + ",</p>"
        "<p>Based on your intake, here's how we'll eliminate <strong>" + pain + "</strong> at <strong>" + company + "</strong>:</p>"
        "<h3 style='color:#5b21b6'>What We'll Build</h3>"
        "<ul>"
        "<li>Automated client reporting (saves 8-12 hrs/week)</li>"
        "<li>AI content brief generator</li>"
        "<li>Lead research & enrichment pipeline</li>"
        "<li>Slack/email notification system</li>"
        "</ul>"
        "<h3 style='color:#5b21b6'>Your Plan: " + plan["name"] + " &mdash; " + plan["price"] + "</h3>"
        "<ul>"
        "<li>Done-for-you build &amp; deployment</li>"
        "<li>Live in 7 days</li>"
        "<li>30-day support included</li>"
        "<li>No calls required</li>"
        "</ul>"
        "<p style='margin-top:32px'>"
        "<a href='" + link + "' style='background:#5b21b6;color:white;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:bold'>"
        + label +
        "</a>"
        "</p>"
        "<p style='margin-top:32px;color:#666;font-size:13px'>Questions? Just reply to this email.<br>"
        "-- " + SENDER_NAME + "</p>"
        "</body></html>"
    )
    return subject, body

def send_email(to_addr, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER_NAME + " <" + GMAIL_USER + ">"
    msg["To"]      = to_addr
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.sendmail(GMAIL_USER, to_addr, msg.as_string())

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            data   = json.loads(body)
            email  = data.get("email", "")
            if not email:
                self._json(400, {"error": "email required"})
                return
            subject, html = build_proposal(data)
            send_email(email, subject, html)
            self._json(200, {"ok": True, "message": "Proposal sent to " + email})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def _json(self, code, obj):
        out = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)
