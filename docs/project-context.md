# Digital Veda Gurukulam ERP & Learning Platform

## Overview

The **Digital Veda Gurukulam ERP & Learning Platform** is a greenfield enterprise application designed to digitally manage a traditional Veda Patasala while preserving the Gurukulam teaching methodology.

The platform combines:

- Patasala Administration
- Learning Management System (LMS)
- Student Information System (SIS)
- Hostel Management
- Community Platform
- Donation & Sponsorship Management
- Multi-Branch Administration

The initial implementation follows a **Modular Monolith Architecture**, allowing future migration to microservices if required.

---

# Project Objectives

The platform supports the following business objectives:

1. Online Admissions
2. Student Management
3. Acharya Management
4. Curriculum Management
5. Learning Content Repository
6. Audio & Video Learning
7. Attendance Tracking
8. Examination & Certification
9. Donations & Sponsorships
10. Community Engagement
11. Alumni Network

---

# Functional Scope

## Admissions

- Online admission application
- Document upload
- Admission review workflow
- Approval / rejection
- Admission reporting

---

## Student Management

- Student profiles
- Parent mapping
- Enrollment
- Academic progress
- Student dashboard

---

## Acharya Management

- Faculty profiles
- Qualification management
- Teaching assignments
- Teaching calendar
- Performance analytics

---

## Curriculum Management

- Course management
- Lesson planning
- Batch planning
- Academic calendar
- Learning path management

---

## Learning Content Repository

Supports:

- Vedic Texts
- PDF Documents
- Audio Repository
- Video Repository
- Search Services

---

## Audio & Video Learning

Features include:

- Streaming lessons
- Practice recording uploads
- Student progress tracking
- AI pronunciation evaluation (Future)

---

## Attendance

- Daily attendance
- Mobile attendance
- Attendance reports

---

## Examination & Certification

- Oral examinations
- Theory examinations
- Marks management
- Transcript generation
- Digital certificates
- Certificate verification

---

## Donations & Sponsorships

Supports:

- Razorpay payment integration
- Student sponsorship
- Acharya sponsorship
- Annadanam donations
- Donor dashboard
- Tax receipts

---

## Community

- Events
- Discussion forums
- Dharma Q&A
- Notification center

---

## Alumni

- Alumni registration
- Alumni directory
- Alumni donations
- Alumni events

---

# Non-Functional Requirements

## Performance

- Page load under 2 seconds
- API response under 500 ms
- Support approximately 100 Monthly Active Users initially
- Designed to scale to 500+ students

## Security

- RBAC
- HTTPS
- JWT Authentication
- MFA for administrators (Future)
- Encryption at rest
- Secure password hashing

## Availability

- Target uptime: 99.5%

## Maintainability

- Modular codebase
- Version-controlled
- Automated CI/CD
- API-first architecture

## Auditability

- Audit logging
- User activity tracking
- Change history
- Log retention

## Backup & Recovery

- Daily database backups
- Media backups
- Disaster recovery planning

## Observability

- CloudWatch
- Grafana
- Centralized logging
- Alerting

## Localization

Supported languages:

- English
- Sanskrit
- Tamil

---

# Feature Mapping


| Business Objective  | Primary Module         |
| ------------------- | ---------------------- |
| Admissions          | Admission Management   |
| Students            | Student Management     |
| Acharyas            | Acharya Management     |
| Curriculum          | Curriculum Management  |
| Learning Repository | Digital Library        |
| Audio / Video       | Media Library          |
| Attendance          | Attendance Management  |
| Examination         | Examination Management |
| Certification       | Certification Engine   |
| Donations           | Donation Management    |
| Community           | Community Portal       |
| Alumni              | Alumni Management      |


---

# Technical Architecture

## Architecture Style

- Modular Monolith

---

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

Purpose:

- Public Website
- Student Portal
- Parent Portal
- Acharya Portal
- Administration Portal

---

## Backend

- Python
- Django
- Django REST Framework

Responsibilities:

- Business Logic
- Authentication
- REST APIs
- Administration

---

## Database

- PostgreSQL

Reason:

- ACID Compliance
- Relational Data
- Strong Django Support

---

## Storage

- AWS S3

Stores:

- Audio
- Video
- PDFs
- Documents

---

## External Integrations

- Razorpay
- WhatsApp Business API
- Zoom / Jitsi
- Email Services

---

## Infrastructure

Cloud Provider:

- AWS (Mumbai Region)

Core Components:

- EC2
- PostgreSQL (RDS)
- S3
- Nginx

---

## DevOps

- Azure DevOps Pipelines
- GitHub Actions (Alternative)
- Docker
- Terraform (Future)

---

## Monitoring

- AWS CloudWatch
- Grafana
- Prometheus (Optional)

---

# Data Model Overview

Core entities include:

- User
- Student
- Parent
- Acharya
- Branch
- Course
- Lesson
- Enrollment
- Batch
- Content
- Attendance
- Examination
- Examination Result
- Certificate
- Donation
- Sponsorship
- Event
- Forum Post
- Comment
- WhatsApp Log

Estimated database size:

- 35–40 core entities

---

# Database Design Principles

- UUID Primary Keys
- Foreign Key Constraints
- Composite Indexes
- Audit Columns
- Soft Delete
- Versioned Migrations

---

# Deployment Strategy

Initial deployment:

- Single EC2
- PostgreSQL
- S3
- Nginx

Future enhancements:

- Load Balancer
- Auto Scaling
- Read Replicas
- CloudFront CDN

---

# Development Principles

- Clean Architecture
- SOLID Principles
- Domain-Driven Design
- API-First Design
- Modular Development
- Enterprise Security
- Auditability
- Scalability

---

# Future Roadmap

- AI Pronunciation Evaluation
- Advanced Search
- Alumni Portal
- Community Forum
- Mobile Applications
- Analytics Dashboard
- Volunteer Management
- Multi-Branch Expansion

---

# Technology Stack Summary


| Layer          | Technology                 |
| -------------- | -------------------------- |
| Frontend       | Next.js, React, TypeScript |
| Backend        | Django, DRF                |
| Database       | PostgreSQL                 |
| Storage        | AWS S3                     |
| Hosting        | AWS EC2                    |
| Reverse Proxy  | Nginx                      |
| CI/CD          | Azure DevOps               |
| Monitoring     | CloudWatch, Grafana        |
| Payments       | Razorpay                   |
| Notifications  | WhatsApp Business API      |
| Video Meetings | Zoom / Jitsi               |


---

# Current Architecture Decision

The project intentionally starts as a **Modular Monolith** because:

- Small initial user base
- Single primary developer
- Faster development
- Lower infrastructure cost
- Easier maintenance

The architecture is designed to evolve into microservices if future scale and operational needs justify that transition.