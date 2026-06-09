from panda3d.core import WindowProperties
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, Vec4
from panda3d.core import ClockObject

class MonPremierJeu3D(ShowBase):
    def __init__(self):
        # 1. Initialise le moteur et ouvre la fenêtre
        super().__init__()

        self.disableMouse()
        self.accept("escape", self.userExit)

       

       # 2. Charge le modèle 3D de décor (inclus de base dans Panda3D)
        self.decor = self.loader.loadModel("models/environment")
        # Attache le modèle à l'univers du jeu (render) pour qu'il soit visible
        self.decor.reparentTo(self.render)

        self.porte = self.loader.loadModel("models/box")
        self.porte.reparentTo(self.render)
        self.porte.setScale(2.0, 0.2, 4.0)
        self.porte.setColor(1.0, 0.0, 0.0, 1.0)
        self.porte.setPos(0, 15, 0)
        

        self.mon_decor = self.loader.loadModel("models/SNAKE/21945_Snake_V1.obj")
        self.mon_decor.reparentTo(self.render)
        self.mon_decor.setPos(0, 15, 0)
        self.mon_decor.setScale(2.0, 0.4, 4.0)

        # Redimensionne et positionne le décor
        self.decor.setScale(0.25, 0.25, 0.25)
        self.decor.setPos(-8, 42, 0)

        # 3. Positionne la caméra de départ
        self.cam.setPos(0, 0, 1.7)
        self.cam.setHpr(0, 0, 0)

        # Touches de mouvement
        self.touches = {"avant": False, "arriere": False, "gauche": False, "droite": False}
        self.accept("z", self.changer_touche, ["avant", True])
        self.accept("z-up", self.changer_touche, ["avant", False])
        self.accept("s", self.changer_touche, ["arriere", True])
        self.accept("s-up", self.changer_touche, ["arriere", False])
        self.accept("q", self.changer_touche, ["gauche", True])
        self.accept("q-up", self.changer_touche, ["gauche", False])
        self.accept("d", self.changer_touche, ["droite", True])
        self.accept("d-up", self.changer_touche, ["droite", False])

        # Souris FPS
        # Rotation avec les touches numériques
        self.heading = 0
        self.pitch = 0
        self.touches_rotation = {"haut": False, "bas": False, "gauche_rot": False, "droite_rot": False}

        self.accept("num4", self.changer_touche, ["gauche_rot", True])
        self.accept("num4-up", self.changer_touche, ["gauche_rot", False])
        self.accept("num6", self.changer_touche, ["droite_rot", True])
        self.accept("num6-up", self.changer_touche, ["droite_rot", False])
        self.accept("num8", self.changer_touche, ["haut", True])
        self.accept("num8-up", self.changer_touche, ["haut", False])
        self.accept("num2", self.changer_touche, ["bas", True])
        self.accept("num2-up", self.changer_touche, ["bas", False])

        self.taskMgr.add(self.mettre_a_jour_souris, "BoucleSouris")

        # Boucles infinies
        self.taskMgr.add(self.mettre_a_jour, "BoucleMouvement")
        

    
        # 4. Ajoute des lumières pour voir les reliefs en 3D
        self.configurer_lumieres()

    def configurer_lumieres(self):
        # Lumière ambiante (évite les ombres totalement noires)
        lum_ambiante = AmbientLight("LumiereAmbiante")
        lum_ambiante.setColor(Vec4(0.5, 0.5, 0.5, 1))
        np_ambiante = self.render.attachNewNode(lum_ambiante)
        self.render.setLight(np_ambiante)

        # Lumière directionnelle (simule le soleil)
        lum_soleil = DirectionalLight("LumiereSoleil")
        lum_soleil.setColor(Vec4(0.8, 0.8, 0.8, 1))
        np_soleil = self.render.attachNewNode(lum_soleil)
        # Oriente le soleil vers le bas et l'avant
        np_soleil.setHpr(0, -45, 0)
        self.render.setLight(np_soleil)

    def changer_touche(self, nom, etat):
        self.touches[nom] = etat

    def mettre_a_jour(self, task):
        from direct.showbase import ShowBase
        dt = ClockObject.getGlobalClock().getDt()
        vitesse = 8.0
        if self.touches["avant"]:   self.cam.setY(self.cam,  vitesse * dt)
        if self.touches["arriere"]: self.cam.setY(self.cam, -vitesse * dt)
        if self.touches["gauche"]:  self.cam.setX(self.cam, -vitesse * dt)
        if self.touches["droite"]:  self.cam.setX(self.cam,  vitesse * dt)
        return task.cont

    def mettre_a_jour_souris(self, task):
        if self.mouseWatcherNode.hasMouse():
            md = self.win.getPointer(0)
            cx, cy = self.win.getXSize()//2, self.win.getYSize()//2
            dx = md.getX() - cx
            dy = md.getY() - cy
            self.heading -= dx * 0.2
            self.pitch   -= dy * 0.2
            self.pitch = max(-80, min(80, self.pitch))
            self.cam.setHpr(self.heading, self.pitch, 0)
            self.win.movePointer(0, cx, cy)
        return task.cont

# Lancement du jeu
jeu = MonPremierJeu3D()
jeu.run()