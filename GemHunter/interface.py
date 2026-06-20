import customtkinter as ctk
from PIL import Image, ImageTk
import tkinter as tk
import time
import subprocess
import sys
from PIL import Image, ImageTk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class IlakakaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ilakaka Madagascar")
        self.geometry("1000x700")
        self.resizable(False, False)
        
        
        bg_image_pil= Image.open(r"C:\Users\USER\Desktop\kilo\models\WhatsApp Image 2026-06-18 at 22.05.56.jpeg")
        bg_image_pil= bg_image_pil.resize((1000, 700), Image.Resampling.LANCZOS)
        bg_image = ImageTk.PhotoImage(bg_image_pil)

        self.bg_label= ctk.CTkLabel(self, image=bg_image, text="")
        self.bg_label.place(x=0 ,y=0, relwidth=1, relheight=1)

        # Variables d'état
        self.sound_on = True
        self.music_on = True
        self.best_score = 15000


        self.frame_main = None
        self.frame_game = None

        self.show_interface1()

    
    def lancer_jeu(self):
        """Affiche un écran de chargement puis lance le jeu Panda3D"""
        # Cacher l'interface actuelle
        if self.frame_game:
            self.frame_game.pack_forget()
        
        # Créer l'écran de chargement
        self.frame_loading = ctk.CTkFrame(self, fg_color="#1a1a1a", width=1000, height=700)
        self.frame_loading.place(x=0, y=0, relwidth=1, relheight=1)
        
        ctk.CTkLabel(
            self.frame_loading, 
            text="ILAKAKA", 
            font=("Impact", 60), 
            text_color="#FFD700"
        ).place(relx=0.5, rely=0.4, anchor="center")
        
        self.label_chargement = ctk.CTkLabel(
            self.frame_loading,
            text="Chargement...",
            font=("Verdana", 20),
            text_color="white"
        )
        self.label_chargement.place(relx=0.5, rely=0.55, anchor="center")
        
        # Barre de progression
        self.barre_chargement = ctk.CTkProgressBar(self.frame_loading, width=400)
        self.barre_chargement.place(relx=0.5, rely=0.65, anchor="center")
        self.barre_chargement.set(0)
        
        # Démarrer l'animation de la barre
        self.progression = 0
        self.animer_chargement()

    def animer_chargement(self):
        self.progression += 0.009
        self.barre_chargement.set(self.progression)
        
        messages = ["Chargement...", "Préparation de la mine...", "Polissage des pierres...", "Presque prêt...", "Bon Jeu Mirary soa"]
        index = min(int(self.progression * len(messages)), len(messages) - 1)
        self.label_chargement.configure(text=messages[index])
        
        if self.progression < 1.0:
            self.after(50, self.animer_chargement)
        else:
            self.destroy()
            subprocess.Popen([sys.executable, "principale.py"])
        
    def on_button_click(self, action):
            if action:
                action()

    def show_interface1(self):
        if self.frame_game: self.frame_game.pack_forget()

        self.frame_main = ctk.CTkFrame(self, fg_color="#8a7602",
                                       border_width=4,
                                       border_color="#ffd700")
        self.frame_main.pack(expand=True, pady=(80,0))

        ctk.CTkLabel(self.frame_main, text="Madagascar", font=("Trebuchet MS", 25), text_color="white").pack()
        ctk.CTkLabel(self.frame_main, text="ILAKAKA", font=("Impact", 90), text_color="#FFD700").pack(pady=(0, 40))

        # CHANGE : "MAIN MENU" appelle show_interface2
        self.btn(self.frame_main, "MAIN MENU", self.show_interface2).pack(pady=10)
        self.btn(self.frame_main, "QUITTER LE JEU", self.quit, color="#941c1c").pack(pady=10)

    def show_interface2(self):
        if self.frame_main: self.frame_main.pack_forget()
    
        self.frame_game = ctk.CTkFrame(self, fg_color=("#3d2b1f"),
                                     corner_radius=40, border_width=3, border_color="#FFD700", width=800, height=400)
        self.frame_game.place(relx=0.5, rely=0.58, anchor="center")

        ctk.CTkLabel(self.frame_game, text="MENU MINE", font=("Impact", 35), text_color="#FFD700").pack(pady=20)

        # CHANGE : "PLAY" lance le jeu Panda3D
        self.btn(self.frame_game, "PLAY", self.lancer_jeu).pack(pady=10)
        
        self.switch_sound = ctk.CTkSwitch(self.frame_game, text="SON", font=("Verdana", 14, "bold"), text_color="white")
        self.switch_sound.select() if self.sound_on else self.switch_sound.deselect()
        self.switch_sound.pack(pady=10)

        self.switch_music = ctk.CTkSwitch(self.frame_game, text="MUSIQUE", font=("Verdana", 14, "bold"), text_color="white")
        self.switch_music.select() if self.music_on else self.switch_music.deselect()
        self.switch_music.pack(pady=10)


        self.btn(self.frame_game, "RETOUR", self.show_interface1, color="#941c1c").pack(pady=30)

    def btn(self, master, text, command, color="#5c4033"):
        return ctk.CTkButton(master, text=text, font=("Verdana", 16, "bold"),
                             fg_color=color, hover_color="#8d6e63",
                             width=250, height=45, corner_radius=10,
                             command=lambda cmd=command: self.on_button_click(command))

    def show_score(self):
        tk.messagebox.showinfo("Records", f"Meilleur score : {self.best_score} Carats")

if __name__ == "__main__":
    app = IlakakaApp()
    app.mainloop()