"""Seed database with initial data for CyberShield 360."""
import os
from datetime import datetime

from models.learning_model import LearningModel
from models.news_model import NewsModel
from models.notification_model import NotificationModel
from models.quiz_model import QuizModel
from models.user_model import UserModel
from utils.database import get_collection
from utils.security import hash_password


def seed_database():
    """Seed database if empty."""
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_name = os.getenv("ADMIN_NAME", "Admin")
    if os.getenv("APP_ENV", "development") != "production":
        admin_email = admin_email or "admin@cybershield360.com"
        admin_password = admin_password or "Admin@123"

    if admin_email and admin_password and not UserModel.find_by_email(admin_email):
        UserModel.create({
            "name": admin_name,
            "email": admin_email.lower().strip(),
            "password": hash_password(admin_password),
            "role": "admin",
            "awareness_score": 100,
            "is_verified": True
        })
        print(f"✓ Admin user created ({admin_email})")
    elif not admin_email or not admin_password:
        print("Admin bootstrap skipped; set ADMIN_EMAIL and ADMIN_PASSWORD to create an admin account.")

    # No demo user is seeded. New users register with their own email.

    # Real cyber news / advisories only
    if get_collection("news").count_documents({}) == 0:
        news_items = [
            {
                "title": "CERT-In warns against AI-driven phishing and impersonation scams",
                "summary": "Indian authorities issued alerts about AI-generated phishing emails and social-engineering campaigns targeting citizens and enterprises.",
                "content": "CERT-In has repeatedly warned that attackers are using AI-generated content to craft highly convincing phishing messages, fake customer support requests, and impersonation scams. The advisory urges organisations to implement MFA, domain security, user awareness training, and rapid incident reporting.",
                "category": "Government",
                "author": "CERT-In",
                "image": "cert-in.jpg",
                "tags": ["cert-in", "phishing", "ai"]
            },
            {
                "title": "RBI amplifies digital payment security guidance for banks and fintechs",
                "summary": "The Reserve Bank of India continues to issue security rules for UPI, cards, and digital banking to reduce fraud and breach risk.",
                "content": "RBI guidance focuses on stronger authentication, transaction monitoring, customer awareness, and mandatory controls for digital payment service providers. Financial institutions are advised to review app security, fraud alerts, and customer verification flows.",
                "category": "Banking",
                "author": "Reserve Bank of India",
                "image": "rbi.jpg",
                "tags": ["rbi", "payments", "banking"]
            },
            {
                "title": "DPDP Act comes into force with new data protection guardrails",
                "summary": "India's Digital Personal Data Protection Act sets rules for consent, processing, breach reporting, and user rights.",
                "content": "The Digital Personal Data Protection Act, 2023 establishes a legal framework for processing personal data in India. Organisations must obtain consent, limit data use, notify affected users of material breaches, and provide clear grievance mechanisms.",
                "category": "Privacy",
                "author": "Government of India",
                "image": "dpdp.jpg",
                "tags": ["dpdp", "privacy", "data protection"]
            },
            {
                "title": "CISA warns of active exploitation against internet-facing systems",
                "summary": "The US Cybersecurity and Infrastructure Security Agency flagged ongoing exploitation of publicly exposed vulnerabilities.",
                "content": "CISA advisories continue to highlight exploitation of edge devices, remote access services, and internet-facing infrastructure. Organisations are urged to patch quickly, restrict exposure, and review monitoring for suspicious login activity.",
                "category": "Security Advisory",
                "author": "CISA",
                "image": "cisa.jpg",
                "tags": ["cisa", "vulnerabilities", "patching"]
            },
            {
                "title": "EU NIS 2 directive strengthens cyber resilience obligations",
                "summary": "The revised EU directive expands cyber risk management and incident reporting expectations for critical sectors.",
                "content": "The NIS 2 Directive strengthens cybersecurity obligations for essential and important entities across the EU, including risk management, resilience testing, and incident reporting requirements designed to improve operational security.",
                "category": "Regulation",
                "author": "European Commission",
                "image": "nis2.jpg",
                "tags": ["eu", "nis2", "cyber resilience"]
            },
            {
                "title": "The Information Technology Act remains the foundation of cybercrime enforcement in India",
                "summary": "The IT Act continues to underpin cybercrime investigation, data protection, and digital offence enforcement in India.",
                "content": "The Information Technology Act, 2000 remains the primary legal framework for cybercrime, identity theft, data misuse, and electronic transaction regulation in India. It continues to guide investigation, prosecution, and compliance measures.",
                "category": "Law",
                "author": "Ministry of Electronics & IT",
                "image": "itact.jpg",
                "tags": ["it act", "india", "cyber law"]
            }
        ]
        for item in news_items:
            NewsModel.create(item)
        print(f"✓ {len(news_items)} real news articles seeded")

    # Learning modules
    if get_collection("learning").count_documents({"type": {"$ne": "cyber_law"}}) == 0:
        modules = [
            {
                "title": "Password Security Fundamentals",
                "description": "Learn how to create strong passwords and manage them securely using password managers.",
                "category": "Password Security",
                "content": "Strong passwords are your first line of defense. Use at least 12 characters with a mix of uppercase, lowercase, numbers, and symbols. Never reuse passwords across sites. Enable two-factor authentication wherever possible. Use a reputable password manager to generate and store unique passwords.",
                "duration": "15 min",
                "type": "article",
                "is_active": True,
                "icon": "fa-key"
            },
            {
                "title": "Recognizing Phishing Attacks",
                "description": "Identify phishing emails, messages, and websites before they compromise your security.",
                "category": "Social Engineering",
                "content": "Phishing attacks trick you into revealing sensitive information. Warning signs include: urgent language, suspicious sender addresses, generic greetings, spelling errors, and unexpected attachments. Always verify requests through official channels. Hover over links to check URLs before clicking.",
                "duration": "20 min",
                "type": "article",
                "is_active": True,
                "icon": "fa-fish"
            },
            {
                "title": "Safe Online Banking Practices",
                "description": "Protect your financial transactions and banking credentials from cyber criminals.",
                "category": "Online Banking",
                "content": "Always access your bank through the official app or by typing the URL directly. Never share OTPs, PINs, or passwords with anyone. Verify UPI transactions in your app, not through screenshots. Report suspicious transactions immediately. Enable transaction alerts on your accounts.",
                "duration": "18 min",
                "type": "article",
                "is_active": True,
                "icon": "fa-university"
            },
            {
                "title": "QR Code Safety Guide",
                "description": "Understand the risks of QR codes and how to scan them safely.",
                "category": "QR Safety",
                "content": "QR codes can hide malicious URLs. Before scanning, check if the QR code has been tampered with (stickers placed over original). Use your phone's built-in scanner which shows the URL before opening. Never scan QR codes from unknown sources. Be especially cautious with payment QR codes.",
                "duration": "12 min",
                "type": "article",
                "is_active": True,
                "icon": "fa-qrcode"
            },
            {
                "title": "Digital Payment Security",
                "description": "Stay safe while using UPI, wallets, and digital payment platforms.",
                "category": "Digital Payments",
                "content": "Verify recipient details before sending money. Use UPI PIN only on official apps. Beware of fake payment screenshots - always check your transaction history. Don't share UPI IDs publicly. Enable biometric authentication. Set transaction limits on your accounts.",
                "duration": "15 min",
                "type": "article",
                "is_active": True,
                "icon": "fa-mobile-alt"
            },
            {
                "title": "Social Engineering Defense",
                "description": "Protect yourself from manipulation tactics used by cyber criminals.",
                "category": "Social Engineering",
                "content": "Social engineering exploits human psychology rather than technical vulnerabilities. Attackers may impersonate IT support, bank officials, or government agents. Always verify identities independently. Never share credentials over phone or chat. Be skeptical of unsolicited contact.",
                "duration": "22 min",
                "type": "article",
                "is_active": True,
                "icon": "fa-user-secret"
            }
        ]
        for mod in modules:
            LearningModel.create(mod)
        print(f"✓ {len(modules)} learning modules seeded")

    # Real cyber law and regulatory content
    if get_collection("learning").count_documents({"type": "cyber_law"}) == 0:
        laws = [
            {
                "title": "Information Technology Act, 2000",
                "description": "India's primary statute governing cybercrime, digital transactions, and electronic evidence.",
                "category": "India",
                "type": "cyber_law",
                "content": "The Information Technology Act, 2000 is the main legal framework for cybercrime and digital commerce in India. It recognizes electronic records, defines offences such as hacking and identity theft, and provides procedures for cyber investigations and digital evidence.",
                "is_active": True
            },
            {
                "title": "CERT-In Directions (Cyber Incident Reporting)",
                "description": "Indian government cybersecurity directions requiring incident reporting and log retention.",
                "category": "India",
                "type": "cyber_law",
                "content": "CERT-In directions require entities to report cybersecurity incidents in a timely manner, retain logs, maintain cybersecurity practices, and coordinate with the national cyber response authority. These directions are essential for cyber resilience and incident response.",
                "is_active": True
            },
            {
                "title": "Digital Personal Data Protection Act, 2023",
                "description": "India's foundational privacy and data protection law for digital personal data.",
                "category": "India",
                "type": "cyber_law",
                "content": "The Digital Personal Data Protection Act, 2023 governs the processing of personal data in India. It focuses on lawful consent, user rights, data fiduciary accountability, breach notification, and data minimization obligations for organisations handling personal data.",
                "is_active": True
            },
            {
                "title": "RBI cyber security framework for banks and payment operators",
                "description": "Reserve Bank of India guidance for secure digital banking, payments, and cyber resilience.",
                "category": "India",
                "type": "cyber_law",
                "content": "RBI mandates banks and digital payment operators to maintain baseline security controls, conduct regular cyber audits, monitor suspicious activity, and implement customer authentication safeguards for digital transactions and electronic banking services.",
                "is_active": True
            },
            {
                "title": "GDPR (General Data Protection Regulation)",
                "description": "EU privacy law governing personal data processing and rights of data subjects.",
                "category": "Global",
                "type": "cyber_law",
                "content": "The General Data Protection Regulation (GDPR) sets strict requirements for personal data processing, consent, security controls, breach notifications, and the rights of individuals to access and control their information in the EU.",
                "is_active": True
            },
            {
                "title": "NIS 2 Directive",
                "description": "EU cybersecurity directive for risk management, resilience, and reporting obligations.",
                "category": "Global",
                "type": "cyber_law",
                "content": "The NIS 2 Directive strengthens cyber resilience obligations across essential and important sectors in the EU. It requires risk management, security measures, incident reporting, and coordination between organisations and national authorities.",
                "is_active": True
            }
        ]
        for law in laws:
            LearningModel.create(law)
        print(f"✓ {len(laws)} real cyber law entries seeded")

    # Quizzes
    if get_collection("quiz").count_documents({}) == 0:
        quizzes = [
            {
                "title": "Cybersecurity Basics Quiz",
                "description": "Test your fundamental cybersecurity knowledge",
                "duration": 300,
                "is_active": True,
                "questions": [
                    {
                        "question": "What is the minimum recommended length for a strong password?",
                        "options": ["6 characters", "8 characters", "12 characters", "4 characters"],
                        "correct": 2
                    },
                    {
                        "question": "What should you do if you receive a suspicious email asking for your bank details?",
                        "options": ["Reply with your details", "Click the link to verify", "Delete and report it", "Forward to friends"],
                        "correct": 2
                    },
                    {
                        "question": "What does OTP stand for in banking security?",
                        "options": ["One Time Password", "Online Transfer Protocol", "Open Transaction Process", "Official Tax Payment"],
                        "correct": 0
                    },
                    {
                        "question": "Which is the safest way to access your bank account online?",
                        "options": ["Click email links", "Use official banking app", "Search on Google and click first result", "Use shared computers"],
                        "correct": 1
                    },
                    {
                        "question": "What is phishing?",
                        "options": ["A type of malware", "Fraudulent attempt to obtain sensitive information", "A firewall technique", "A password manager"],
                        "correct": 1
                    },
                    {
                        "question": "Should you share your OTP with anyone claiming to be from your bank?",
                        "options": ["Yes, if they know your account number", "Yes, for verification purposes", "No, never share OTP with anyone", "Only with family members"],
                        "correct": 2
                    },
                    {
                        "question": "What is two-factor authentication (2FA)?",
                        "options": ["Using two passwords", "An extra security layer requiring two verification methods", "Having two email accounts", "Logging in twice"],
                        "correct": 1
                    },
                    {
                        "question": "How can you verify if a website is secure for transactions?",
                        "options": ["Check for colorful design", "Look for HTTPS and padlock icon", "Count the number of ads", "Check social media followers"],
                        "correct": 1
                    },
                    {
                        "question": "What should you do before scanning an unknown QR code?",
                        "options": ["Scan immediately", "Check the URL it will open", "Share with friends first", "Take a screenshot"],
                        "correct": 1
                    },
                    {
                        "question": "Which organization handles cybersecurity incidents in India?",
                        "options": ["ISRO", "CERT-In", "NPCI", "TRAI"],
                        "correct": 1
                    }
                ]
            },
            {
                "title": "Phishing Detection Challenge",
                "description": "Advanced quiz on identifying phishing and scam attempts",
                "duration": 240,
                "is_active": True,
                "questions": [
                    {
                        "question": "An email from 'paypa1-secure@gmall.com' asking to verify your account is:",
                        "options": ["Legitimate", "A phishing attempt", "A marketing email", "An automated notification"],
                        "correct": 1
                    },
                    {
                        "question": "A message saying 'Your SBI account will be blocked in 2 hours. Click here to verify' is:",
                        "options": ["Urgent bank notification", "A scam using urgency tactics", "A routine security check", "A customer service message"],
                        "correct": 1
                    },
                    {
                        "question": "Which URL is most likely a phishing site?",
                        "options": ["https://www.hdfcbank.com", "https://hdfc-bank-verify.tk/login", "https://www.onlinesbi.sbi", "https://www.icicibank.com"],
                        "correct": 1
                    },
                    {
                        "question": "A WhatsApp message claiming you won a lottery you never entered is:",
                        "options": ["Good news", "A lottery scam", "A promotional offer", "A government scheme"],
                        "correct": 1
                    },
                    {
                        "question": "Someone calls claiming to be from IT support asking for remote access to your computer. You should:",
                        "options": ["Grant access immediately", "Ask for their employee ID and verify independently", "Share your password for verification", "Install software they recommend"],
                        "correct": 1
                    }
                ]
            }
        ]
        for quiz in quizzes:
            QuizModel.create(quiz)
        print(f"✓ {len(quizzes)} quizzes seeded")

    # Notifications
    if get_collection("notifications").count_documents({}) == 0:
        alerts = [
            {
                "title": "Critical: New UPI Scam Alert",
                "message": "Fraudsters are sending fake payment screenshots via WhatsApp. Always verify in your banking app.",
                "type": "scam_alert",
                "priority": "high",
                "is_global": True
            },
            {
                "title": "CERT-In Advisory: Log4j Vulnerability",
                "message": "CERT-In has issued advisory for Log4j vulnerability. Update affected systems immediately.",
                "type": "government_alert",
                "priority": "high",
                "is_global": True
            },
            {
                "title": "Cyber Awareness Week 2026",
                "message": "Join our Cyber Awareness Week activities. Complete quizzes and earn certificates!",
                "type": "breaking_news",
                "priority": "medium",
                "is_global": True
            },
            {
                "title": "New Learning Module Available",
                "message": "Check out our new 'Digital Payment Security' learning module.",
                "type": "cyber_warning",
                "priority": "low",
                "is_global": True
            }
        ]
        for alert in alerts:
            NotificationModel.create(alert)
        print(f"✓ {len(alerts)} notifications seeded")

    print("Database seeding complete!")
