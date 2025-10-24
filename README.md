# Team Sync

**Team Sync** is a comprehensive **team collaboration and project management tool**, designed to streamline task tracking, sprint planning, and team communication. Inspired by tools like **Jira**, Team Sync focuses on clean UI, role-based control, and real-time collaboration features such as chat and video calls — all while supporting multi-workspace workflows.

---

## 🌟 Key Features

- 🧠 **Workspace Management**
  - Create personal or company workspaces (with Stripe subscriptions).
  - Add members and manage roles (Owner, Manager, Developer).
  - Switch between multiple workspaces.

- 📂 **Projects & Backlog**
  - Each workspace contains multiple projects.
  - Projects contain **Epics** (big features).
  - Epics contain **Stories** (tasks or bugs).

- 📆 **Sprints**
  - Plan and start sprints with prioritized stories.
  - Visual board with status columns: `To-Do`, `In Progress`, `Review`, `Done`.
  - Restrict sprint start if epics lack stories.
  - Prevent sprint completion unless all stories are done.

- 🔄 **Drag & Drop Interface**
  - Rearrange stories across columns using drag-and-drop.
  - Supports reordering and real-time status updates.

- 🎥 **Collaboration**
  - One-on-one and group chat support within projects.
  - Video call integration for team meetings.

- 💳 **Billing & Subscriptions**
  - Stripe integration for workspace plans.
  - Workspace is created only after successful Stripe checkout.

- 👥 **Role-Based Access Control (RBAC)**
  - Access and permissions based on role within workspace and project.

- 🗒 **User Settings**
  - Update profile information and password.
  - Manage subscription.
  - Upload profile pictures.

---

## 🔐 Authentication & Security

- JWT-based login with refresh tokens.
- Secure logout that clears all Redux and local/session storage.
- Protected routes and role-aware UI components.

---

## 🛠️ Tech Stack

- **Frontend:** React + Vite + Tailwind CSS
- **State Management:** Redux Toolkit + Redux Persist
- **Authentication:** JWT (Access & Refresh tokens)
- **Payments:** Stripe
- **Backend:** Django + DRF
- **Database:** PostgreSQL
- **Real-Time:** WebSocket-based Chat & Video (via WebRTC/Socket.io)
- **Deployment:** Vercel / Netlify (Frontend) + Render / Railway (Backend)

---

## 🧪 Getting Started

### Backend Setup

```bash
# Clone the repo
git clone https://github.com/your-username/team-sync.git

# Move into the backend directory
cd team-sync/backend

# Create and activate a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy the sample environment file and update it
cp .env.sample .env

# Apply migrations
python manage.py migrate

# Run the development server
python manage.py runserver
```

### Frontend Setup

```bash
# Move into the frontend directory
cd team-sync/frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

---

## ⚙️ Environment Configuration

Create a `.env` file in the backend directory with the following variables:

```env
# ===============================
# EMAIL SETTINGS
# ===============================
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=your_email@example.com

# ===============================
# DATABASE SETTINGS
# ===============================
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# ===============================
# DJANGO SETTINGS
# ===============================
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# ===============================
# CORS SETTINGS
# ===============================
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173

# ===============================
# SOCIAL AUTH (Google OAuth)
# ===============================
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your_google_client_id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your_google_client_secret

# ===============================
# STRIPE SETTINGS
# ===============================
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLIC_KEY=your_stripe_public_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret

# ===============================
# CLOUDINARY SETTINGS
# ===============================
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_cloud_api_key
CLOUDINARY_API_SECRET=your_cloud_api_secret
CLOUDINARY_URL=your_cloudinary_url
```

---

## 🧱 Backend API Summary

The Django + DRF backend provides API endpoints for:

- User registration, login, logout
- Workspace, Project, Epic, Story CRUD operations
- Sprint start/completion logic
- Chat and video management
- Stripe webhook integration

---

## 📈 Future Enhancements

- Notification system (email + in-app)
- Admin dashboard for usage metrics
- Mobile app (React Native or Flutter)
- Third-party integrations (Slack, GitHub, Notion)

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).

---

## ✨ About the Developer

Built with ❤️ by **Aswin Narayanan**  
BSc Mathematics graduate turned self-taught full-stack developer. Passionate about problem-solving, scalable systems, and building tools that help teams collaborate better.

[LinkedIn](https://www.linkedin.com/in/aswin-nt/) • [Email](mailto:aswinmalamakkavu@gmail.com)

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/your-username/team-sync/issues).

## ⭐ Show Your Support

Give a ⭐️ if this project helped you!