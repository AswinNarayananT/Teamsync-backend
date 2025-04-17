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
- **Backend (Connected):** Django + DRF
- **Database:** PostgreSQL
- **Real-Time:** WebSocket-based Chat & Video (via WebRTC/Socket.io)
- **Deployment:** Vercel / Netlify (Frontend) + Render / Railway (Backend)

---

## 🧪 Getting Started

```bash
# Clone the repo
git clone https://github.com/your-username/team-sync.git

# Install dependencies
cd team-sync
npm install

# Run the development server
npm run dev
```

Visit: [http://localhost:5173](http://localhost:5173)

---

## 🧱 Backend Summary (API)

- Django + DRF backend
- API endpoints for:
  - User registration, login, logout
  - Workspace, Project, Epic, Story CRUD
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

[LinkedIn](www.linkedin.com/in/aswin-nt/) •  [Email](aswinmalamakkavu@gmail.com)

