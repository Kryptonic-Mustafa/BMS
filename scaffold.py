import os
import json

# --- Configuration ---
PROJECT_NAME = "."  # Current directory
# Strict 4-Color Palette Hex Codes
COLORS = {
    "primary": "#1E3A8A",    # Deep Indigo / Royal Blue (blue-900)
    "secondary": "#0D9488",  # Teal / Cyan Accent (teal-600)
    "background": "#F8FAFC", # Light Gray / Off White (slate-50)
    "neutral": "#334155",    # Dark Gray / Slate (slate-700)
    "danger": "#EF4444",     # Red for errors
    "success": "#10B981"     # Green for success
}

# --- File Contents ---

# 1. package.json
package_json = {
  "name": "bank-management-system",
  "version": "0.1.0",
  "private": True,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "latest",
    "react": "latest",
    "react-dom": "latest",
    "lucide-react": "latest",  # Icons
    "clsx": "latest",
    "tailwind-merge": "latest",
    "mysql2": "latest",        # For TiDB/MySQL
    "server-only": "latest"
  },
  "devDependencies": {
    "@types/node": "latest",
    "@types/react": "latest",
    "@types/react-dom": "latest",
    "autoprefixer": "latest",
    "postcss": "latest",
    "tailwindcss": "latest",
    "typescript": "latest"
  }
}

# 2. tsconfig.json
tsconfig_json = {
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": True,
    "skipLibCheck": True,
    "strict": True,
    "noEmit": True,
    "esModuleInterop": True,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": True,
    "isolatedModules": True,
    "jsx": "preserve",
    "incremental": True,
    "plugins": [{"name": "next"}],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}

# 3. tailwind.config.ts
tailwind_config = f"""
import type {{ Config }} from "tailwindcss";

const config: Config = {{
  content: [
    "./pages/**/*.{{js,ts,jsx,tsx,mdx}}",
    "./components/**/*.{{js,ts,jsx,tsx,mdx}}",
    "./app/**/*.{{js,ts,jsx,tsx,mdx}}",
  ],
  theme: {{
    extend: {{
      colors: {{
        primary: {{
          DEFAULT: "{COLORS['primary']}",
          foreground: "#FFFFFF",
        }},
        secondary: {{
          DEFAULT: "{COLORS['secondary']}",
          foreground: "#FFFFFF",
        }},
        background: "{COLORS['background']}",
        neutral: "{COLORS['neutral']}",
        danger: "{COLORS['danger']}",
        success: "{COLORS['success']}",
      }},
      borderRadius: {{
        lg: "0.5rem",
        xl: "0.75rem",
        "2xl": "1rem",
      }},
      boxShadow: {{
        'soft': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
      }}
    }},
  }},
  plugins: [],
}};
export default config;
"""

# 4. postcss.config.js
postcss_config = """
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""

# 5. app/globals.css
globals_css = f"""
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {{
  body {{
    @apply bg-background text-neutral antialiased;
  }}
  h1, h2, h3, h4, h5, h6 {{
    @apply font-bold tracking-tight text-primary;
  }}
}}

@layer components {{
  .btn-primary {{
    @apply bg-primary text-white px-4 py-2 rounded-lg hover:bg-opacity-90 transition-all duration-200 shadow-sm font-medium;
  }}
  .card {{
    @apply bg-white rounded-xl shadow-soft border border-slate-100 p-6;
  }}
  .input-field {{
    @apply w-full px-4 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all;
  }}
}}
"""

# 6. app/layout.tsx
layout_tsx = """
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Modern Banking System",
  description: "Production grade banking application",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
"""

# 7. Placeholder for Page (app/page.tsx)
page_tsx = """
import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-background">
      <div className="text-center space-y-6">
        <h1 className="text-5xl font-bold text-primary">Bank Management System</h1>
        <p className="text-xl text-neutral/80">Secure. Modern. Reliable.</p>
        <div className="flex gap-4 justify-center mt-8">
          <Link href="/login" className="btn-primary">Login</Link>
          <Link href="/register" className="px-4 py-2 rounded-lg border border-primary text-primary hover:bg-primary/5 transition-all">Register</Link>
        </div>
      </div>
    </main>
  );
}
"""

# --- Directory Structure Definition ---
structure = {
    "app": {
        "(auth)": {
            "login": {"page.tsx": "// Login Page"},
            "register": {"page.tsx": "// Register Page"},
            "layout.tsx": "// Auth Layout"
        },
        "(dashboard)": {
            "admin": {
                "page.tsx": "// Admin Dashboard Home",
                "customers": {"page.tsx": "// Customer Management"},
                "accounts": {"page.tsx": "// Account Management"},
                "transactions": {"page.tsx": "// Transaction Reports"}
            },
            "customer": {
                "page.tsx": "// Customer Dashboard Home",
                "transfer": {"page.tsx": "// Money Transfer"},
                "history": {"page.tsx": "// Transaction History"}
            },
            "layout.tsx": "// Dashboard Layout (Sidebar + Navbar)"
        },
        "api": {
            "auth": {"route.ts": "// Auth API Handler"},
            "customers": {"route.ts": "// Customer API"},
            "transactions": {"route.ts": "// Transaction API"}
        },
        "globals.css": globals_css,
        "layout.tsx": layout_tsx,
        "page.tsx": page_tsx
    },
    "components": {
        "ui": {
            "Button.tsx": "// Reusable Button Component",
            "Card.tsx": "// Card Component",
            "Input.tsx": "// Input Component",
            "Badge.tsx": "// Badge Component",
            "Table.tsx": "// Data Table Component",
            "Alert.tsx": "// Alert Component"
        },
        "forms": {
            "LoginForm.tsx": "// Login Form",
            "RegisterForm.tsx": "// Register Form",
            "TransferForm.tsx": "// Money Transfer Form"
        },
        "layout": {
            "Sidebar.tsx": "// Dashboard Sidebar",
            "Navbar.tsx": "// Top Navigation",
            "MobileMenu.tsx": "// Responsive Menu"
        }
    },
    "lib": {
        "db.ts": "// TiDB / MySQL Connection",
        "utils.ts": "// Helper functions",
        "auth.ts": "// Auth logic"
    },
    "services": {
        "userService.ts": "// User business logic",
        "accountService.ts": "// Account business logic"
    },
    "types": {
        "index.ts": "// Global TypeScript interfaces"
    },
    "hooks": {
        "useAuth.ts": "// Auth hook"
    }
}

# --- Helper Function to Create Structure ---
def create_structure(base_path, structure_dict):
    for name, content in structure_dict.items():
        path = os.path.join(base_path, name)
        
        if isinstance(content, dict):
            # It's a directory
            if not os.path.exists(path):
                os.makedirs(path)
            create_structure(path, content)
        else:
            # It's a file
            with open(path, 'w') as f:
                f.write(content)

# --- Main Execution ---
def main():
    print(f"🚀 Initializing Bank Management System in {os.path.abspath(PROJECT_NAME)}...")
    
    # Create Directories and Files
    create_structure(PROJECT_NAME, structure)
    
    # Create Root Config Files
    with open("package.json", "w") as f:
        json.dump(package_json, f, indent=2)
        
    with open("tsconfig.json", "w") as f:
        json.dump(tsconfig_json, f, indent=2)
        
    with open("tailwind.config.ts", "w") as f:
        f.write(tailwind_config)
        
    with open("postcss.config.js", "w") as f:
        f.write(postcss_config)
        
    # Create .gitignore
    with open(".gitignore", "w") as f:
        f.write("node_modules\n.next\n.env\n.DS_Store\n")

    print("✅ Project scaffolding complete!")
    print("👉 Next Steps:")
    print("1. Run 'npm install'")
    print("2. Run 'npm run dev' to see the login landing page.")

if __name__ == "__main__":
    main()