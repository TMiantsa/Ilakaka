import customtkinter as ctk
import subprocess
import sys

ctk.set_appearance_mode("dark")

class SplashScreen(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ilakaka")
        self.geometry("1000x700")
        self.resizable(False, False)
        
        
        
        # Centrer la fenêtre à l'écran
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - 300
        y = (screen_height // 2) - 200
        self.geometry(f"600x400+{x}+{y}")

        self.configure(fg_color="#1a1a1a")

        ctk.CTkLabel(
            self, 
            text="ILAKAKA", 
            font=("Impact", 70), 
            text_color="#FFD700"
        ).place(relx=0.5, rely=0.35, anchor="center")

        ctk.CTkLabel(
            self,
            text="Madagascar",
            font=("Trebuchet MS", 22),
            text_color="white"
        ).place(relx=0.5, rely=0.5, anchor="center")

        

        self.label_chargement = ctk.CTkLabel(
            self,
            text="Chargement...",
            font=("Verdana", 16),
            text_color="#cccccc"
        )
        self.label_chargement.place(relx=0.5, rely=0.65, anchor="center")

        self.barre_chargement = ctk.CTkProgressBar(self, width=400)
        self.barre_chargement.place(relx=0.5, rely=0.75, anchor="center")
        self.barre_chargement.set(0)

        self.progression = 0
        self.animer_chargement()

        

    def animer_chargement(self):
        self.progression += 0.009
        self.barre_chargement.set(self.progression)

        if self.progression < 1.0:
            self.after(50, self.animer_chargement)
        else:
            self.destroy()
            subprocess.Popen([sys.executable, "interface.py"])

if __name__ == "__main__":
    app = SplashScreen()
    app.mainloop()