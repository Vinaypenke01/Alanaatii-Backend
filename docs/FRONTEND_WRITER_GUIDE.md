# ✍️ Exhaustive Writer Frontend Guide

This document contains every single endpoint available to the **Writer Role**.

**Base URL:** `http://localhost:8000/api/v1`
**Header:** `Authorization: Bearer <token>`

---

## 1. Authentication
- **POST** `/auth/writer/login/`
- **Payload:**
  ```json
  { "email": "writer@alanaatii.com", "password": "..." }
  ```

## 2. Profile Management

### View Profile
- **GET** `/writer/profile/`
- **Response:** `{ "id": "...", "full_name": "...", "email": "...", "phone_wa": "...", "languages": ["English", "Hindi"] }`

### Update Profile
- **PUT** `/writer/profile/`
- **Payload:** `{ "phone_wa": "918887776655", "full_name": "New Writer Name" }`

---

## 2. Assignment Actions

### Accept Assignment
- **POST** `/writer/assignments/<id>/accept/`
- **Payload:** `{}` (Moves order to accepted status).

### Decline Assignment
- **POST** `/writer/assignments/<id>/decline/`
- **Payload:**
  ```json
  { "reason": "Too busy with other orders this week." }
  ```

---

## 3. Creative Workflow

### Save Working Draft
- **PUT** `/writer/orders/<id>/draft/`
- **Payload:**
  ```json
  { "draft_content": "Dear Father, I am writing this to express..." }
  ```

### Submit Final Script
- **POST** `/writer/orders/<id>/submit-script/`
- **Payload:**
  ```json
  {
    "content": "Final finalized letter text...",
    "writer_note": "Focused on the gratitude aspect as requested."
  }
  ```

---

## 4. Notifications
- **PATCH** `/notifications/<id>/read/`: Mark single notification as read.
- **POST** `/notifications/read-all/`: Mark all notifications as read.
- **Payload:** `{}`
