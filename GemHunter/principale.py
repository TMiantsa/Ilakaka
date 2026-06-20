import math
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import (
    CollisionTraverser, CollisionNode, CollisionBox, CollisionSphere,
    CollisionHandlerEvent, CollisionHandlerPusher,
    CollisionRay, CollisionHandlerQueue,
    Point3, Vec3, Vec4,
    WindowProperties, ClockObject, TextNode,
    AmbientLight, DirectionalLight
)
from panda3d.core import ClockObject
globalClock = ClockObject.getGlobalClock()
globalClock.setMode(ClockObject.MLimited)
globalClock.setFrameRate(60)
from direct.actor.Actor import Actor
import random
from panda3d.core import CardMaker, Texture



class BoutiquePierres(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()

        self.alerte_active = False

        # --- Masques de collision (qui peut toucher quoi) ---
        self.MASQUE_SOL   = 0x02
        self.MASQUE_JOUEUR = 0x01
        self.MASQUE_ROCHE  = 0x04   # nouveau : masque dédié aux pierres
        self.MASQUE_MINERAI = 0x08

        #===============================================================
        #Nom du jeux ecrit sur le demarrage
        #===============================================================
        wp = WindowProperties()
        wp.setTitle("Ilakaka Game")
        self.win.requestProperties(wp)

        #===============================================================
        #Texture du sol
        #===============================================================
        self.ground_texture = self.loader.loadTexture("models/ground1.jpg")

        self.win.requestProperties(WindowProperties.size(1000, 700))

        self.set_background_color(0.53, 0.81, 0.98)

        #===============================================================
        #Petite commande pour voir FPS en temps reel
        #===============================================================
        self.setFrameRateMeter(True)   # voir les FPS en temps réel
        globalClock.setMode(ClockObject.MLimited)
        globalClock.setFrameRate(60)   # limiter à 60 FPS

        self.camLens.setFar(100)    # ne rend que ce qui est à moins de 200 unités
        self.camLens.setNear(0.1)

        

        # Configuration de la lumière
        alight = AmbientLight("ambiant")
        alight.setColor(Vec4(0.6, 0.6, 0.6, 1))
        self.render.setLight(self.render.attachNewNode(alight))

        # Configuration de la lumière directionnelle
        dlight = DirectionalLight("directionnel")
        dlight.setColor(Vec4(1.0, 0.75, 0.5, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(45, -45, 0)
        self.render.setLight(dlnp)

        #==========================================================
        # Chargement du sol
        #===========================================================
        cm = CardMaker("sol")
        cm.setFrame(-200, 200, -200, 200)
        self.noeud_sol = self.render.attachNewNode("groupe_sol")
        sol = self.noeud_sol.attachNewNode(cm.generate())
        sol.setP(-90)
        sol.setCollideMask(self.MASQUE_SOL)
        sol.setTexture(self.ground_texture)

        #=========================================================
        #Impose limite carte
        #====================================================
        limite_carte = 95
        murs = [
            ( limite_carte, 0, 1, 200, 0),      # mur EST
            (-limite_carte, 0, 1, 200, 0),      # mur OUEST
            (0,  limite_carte, 200, 1, 90),     # mur NORD
            (0, -limite_carte, 200, 1, 90),     # mur SUD
        ]

        for (mx, my, largeur, profondeur, rotation) in murs:
            # Partie visuelle (boîte texturée en pierre)
    
            # Partie collision seulement (sans bloc visuel)
            noeud_mur = CollisionNode(f"mur_{mx}_{my}")
            noeud_mur.addSolid(
                CollisionBox(Point3(0, 0, 0), largeur/2, profondeur/2, 12)
            )
            noeud_mur.setIntoCollideMask(self.MASQUE_ROCHE)
            noeud_mur.setFromCollideMask(0)
            mur_np = self.render.attachNewNode(noeud_mur)
            mur_np.setPos(mx, my, 6)

            noeud_detect = CollisionNode(f"mur_detect_{mx}_{my}")
            noeud_detect.addSolid(
                CollisionBox(Point3(0, 0, 0), largeur/2, profondeur/2, 12)
            )
            noeud_detect.setIntoCollideMask(0x08)  # masque spécial pour les murs
            noeud_detect.setFromCollideMask(0)
            detect_np = self.render.attachNewNode(noeud_detect)
            detect_np.setPos(mx, my, 6)

        self.accept("into-mur_detect-*", self.touche_mur)

        # ================================================================
        # MINERAIS — état global
        # ================================================================
        self.liste_minerais = []      # liste de dicts {node, pv, vibration_timer, pos_base}
        self.inventaire = {"emeraude": 0, "rubis": 0, "saphir": 0}
        self.distance_minage = 5.0    # distance maximale pour miner
        self.cooldown_minage = 0.4    # secondes entre deux coups
        self.timer_minage    = 0.0    # temps restant avant prochain coup autorisé
        self.pioche_active   = True   # le joueur a une pioche

        self.placer_minerais_aleatoirement(30)  # 30 gisements en tout


        
        #========================================================
        # Charge une image de montagnes (PNG/JPG avec un horizon)
        #========================================================
        self.fond_montagnes = self.loader.loadTexture("models/fond_desert.jpg")

        cm_fond = CardMaker("fond_montagnes")
        cm_fond.setFrame(-400, 400, 0, 150)   # large et pas trop haut

        self.noeud_fond = self.render.attachNewNode("fond_lointain")
        fond = self.noeud_fond.attachNewNode(cm_fond.generate())
        fond.setTexture(self.fond_montagnes)
        fond.setColor(0.6, 0.7, 0.85, 1)
        fond.setPos(0, 300, -20)    # très loin derrière, légèrement abaissé
        fond.setLightOff()           # pas affecté par les lumières (reste net/visible)
        fond.setBin("background", 0)
        fond.setDepthWrite(False)

        #====================================
        #les roches
        #====================================
        self.placer_roches_aleatoirement(150)


        # Configuration initiale de la caméra et du joueur
        self.heading       = 180.0
        self.pitch         = 20.0
        self.cam_distance  = 10.0
        self.souris_active = False

        # Configuration initiale du joueur(z)

        self.hauteur_joueur    = 1.0

        # Configuration du modèle du joueur
        self.joueur_pivot = self.render.attachNewNode("joueur_pivot")
        self.joueur = self.loader.loadModel("models/Man.egg")
        self.joueur.reparentTo(self.joueur_pivot)
        self.joueur_pivot.setPos(20, 20, -50)
        self.joueur.setPos(0, 0, -1.0) # Ajustement de la flottaison (Z)
        self.joueur.setH(180)         
        self.joueur.setScale(0.5)

        # Configuration des collisions
        self.cTrav       = CollisionTraverser("traverser")
        self.cEvent      = CollisionHandlerEvent()
        self.sol_handler = CollisionHandlerQueue()

        ray = CollisionRay()
        ray.setOrigin(0, 0, 50)
        ray.setDirection(0, 0, -1)

        ray_node = CollisionNode("ray_sol")
        ray_node.addSolid(ray)
        ray_node.setFromCollideMask(self.MASQUE_SOL)
        ray_node.setIntoCollideMask(0)

        self.ray_np = self.joueur.attachNewNode(ray_node)
        self.cTrav.addCollider(self.ray_np, self.sol_handler)

        # Collider pour repousser physiquement (pierres/rochers)
        sphere_joueur = CollisionSphere(0, 0, 0, 0.8)
        noeud_joueur  = CollisionNode("joueur")
        noeud_joueur.addSolid(sphere_joueur)
        noeud_joueur.setFromCollideMask(self.MASQUE_ROCHE)
        noeud_joueur.setIntoCollideMask(0x00)
        self.joueur_col = self.joueur.attachNewNode(noeud_joueur)

        self.pousseur = CollisionHandlerPusher()
        self.pousseur.addCollider(self.joueur_col, self.joueur_pivot)
        self.pousseur.setHorizontal(True)
        self.cTrav.addCollider(self.joueur_col, self.pousseur)

        # Collider SÉPARÉ pour détecter les murs (événements seulement)
        sphere_detect = CollisionSphere(0, 0, 0, 0.8)
        noeud_detect_joueur = CollisionNode("joueur_detect_mur")
        noeud_detect_joueur.addSolid(sphere_detect)
        noeud_detect_joueur.setFromCollideMask(0x08)
        noeud_detect_joueur.setIntoCollideMask(0x00)
        self.joueur_detect_col = self.joueur.attachNewNode(noeud_detect_joueur)

        self.cEvent.addInPattern("into-mur_detect-*")
        self.cTrav.addCollider(self.joueur_detect_col, self.cEvent)

        #============================================================
        #adaptation avec souri
        #============================================================
        self.cam.setPos(self.joueur_pivot.getPos() + Vec3(0, -10, 5))
        self.cam.lookAt(self.joueur_pivot)
        self.capturer_souris(True)

        #=============================================================
        # Chargement de Ralph avec animation
        #=============================================================
        self.pnj = Actor("models/ralph.egg.pz", {
    "run": "models/ralph-run.egg.pz"
        })
        self.pnj.reparentTo(self.render)
        self.pnj.setPos(24, -27, 2)
        self.pnj.setScale(1, 1, 1)
        self.pnj.loop("run")

        # Rayon de collision pour que Ralph suive le sol
        ray_pnj = CollisionRay()
        ray_pnj.setOrigin(0, 0, 50)
        ray_pnj.setDirection(0, 0, -1)

        ray_node_pnj = CollisionNode("ray_pnj")
        ray_node_pnj.addSolid(ray_pnj)
        ray_node_pnj.setFromCollideMask(self.MASQUE_SOL)
        ray_node_pnj.setIntoCollideMask(0)

        self.ray_pnj_np = self.pnj.attachNewNode(ray_node_pnj)
        self.pnj_handler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.ray_pnj_np, self.pnj_handler)

        self.z_pnj = 2.0
        self.pnj_direction = 0.0      # angle de marche du PNJ
        self.pnj_vitesse   = 8.0      # vitesse de déplacement
        self.pnj_timer     = 0.0      # compteur avant prochain changement
        self.pnj_interval  = 3.0      # changer de direction toutes les 3 sec

        #================================================================
        # Configuration des touches
        #================================================================
        self.touches = {
            "avant": False, "arriere": False,
            "gauche": False, "droite": False,
        }
        self.accept("z",    self.changer_touche, ["avant",   True])
        self.accept("z-up", self.changer_touche, ["avant",   False])
        self.accept("s",    self.changer_touche, ["arriere", True])
        self.accept("s-up", self.changer_touche, ["arriere", False])
        self.accept("q",    self.changer_touche, ["gauche",  True])
        self.accept("q-up", self.changer_touche, ["gauche",  False])
        self.accept("d",    self.changer_touche, ["droite",  True])
        self.accept("d-up", self.changer_touche, ["droite",  False])
        self.accept("mouse1", self.on_clic_gauche)
        self.accept("escape", self.retour_menu)

        # ================================================================
        # HUD
        # ================================================================
        self.texte_pos = OnscreenText(
            text="", pos=(-1.3, -0.92), scale=0.05,
            fg=(1, 1, 1, 1), align=TextNode.ALeft
        )

        self.texte_alerte = OnscreenText(
            text="", pos=(0, 0.5), scale=0.08,
            fg=(1, 0, 0, 1), align=TextNode.ACenter,
            shadow=(0, 0, 0, 1)
        )
        # Texte inventaire minerais
        self.texte_minerais = OnscreenText(
            text="", pos=(-1.3, 0.90), scale=0.055,
            fg=(0.2, 1.0, 0.4, 1), align=TextNode.ALeft,
            shadow=(0, 0, 0, 1)
        )
        # Texte pioche / action
        self.texte_action = OnscreenText(
            text="⛏  [Clic gauche] pour miner", pos=(0, -0.85), scale=0.055,
            fg=(1, 0.85, 0.2, 1), align=TextNode.ACenter,
            shadow=(0, 0, 0, 1)
        )



        #  Configuration de l'interface utilisateur
        self.texte_pos = OnscreenText(
            text="", pos=(-1.3, -0.92), scale=0.05,
            fg=(1, 1, 1, 1), align=TextNode.ALeft
        )

        #====================================================
        #tsy dia ilaina
        #====================================================
        self.vue_haut = False
        self.accept("v", self.basculer_vue)   # touche V pour basculer

        self.taskMgr.add(self.mettre_a_jour, "BouclePrincipale")

        


        self.z_sol_actuel = 1.0
        self.taskMgr.add(self.mettre_a_jour, "BouclePrincipale")
        self.taskMgr.add(self.mettre_a_jour_vibrations, "Vibrations")


#==============================================================
#LIGNE DES DEFINITION
#==============================================================

    TYPES_MINERAIS = [
        {"nom": "emeraude", "fichier": "models/emeuraude.glb"},
        {"nom": "rubis",    "fichier": "models/ruby.glb"},
        {"nom": "saphir",   "fichier": "models/Saphire.glb"},
    ]

    #************************************************************
    #LES PIERRES PRECIEUSE
    #*************************************************************
    def placer_minerais_aleatoirement(self, nombre):
        """Spawne des gisements de minerais comme les roches."""
        zone_reservee_centre = (0, 0)
        zone_reservee_rayon  = 8

        for i in range(nombre):
            # Position valide (hors zone réservée)
            for _ in range(30):
                x = random.uniform(-85, 85)
                y = random.uniform(-85, 85)
                dist = math.hypot(x - zone_reservee_centre[0],
                                  y - zone_reservee_centre[1])
                if dist > zone_reservee_rayon:
                    break

            type_minerai = random.choice(self.TYPES_MINERAIS)
            scale    = random.uniform(0.8, 1.8)
            rotation = random.uniform(0, 360)

            try:
                noeud = self.loader.loadModel(type_minerai["fichier"])
            except Exception:
                continue  # si le modèle est absent, on passe

            noeud.reparentTo(self.render)
            pos_base = Point3(x, y, 0.3)
            noeud.setPos(pos_base)
            noeud.setScale(scale)
            noeud.setH(rotation)

            # Sphère de collision (bloque le joueur aussi)
            limites = noeud.getTightBounds(noeud)
            if limites:
                pmin, pmax = limites
                centre_col = (pmin + pmax) * 0.5
                rayon_col  = (pmax - pmin).length() * 0.35
                rayon_col  = max(rayon_col, 0.5)
            else:
                centre_col = Point3(0, 0, 0)
                rayon_col  = 0.8

            noeud_col = CollisionNode(f"minerai_col_{i}")
            noeud_col.addSolid(
                CollisionSphere(centre_col.getX(), centre_col.getY(),
                                centre_col.getZ(), rayon_col)
            )
            noeud_col.setIntoCollideMask(self.MASQUE_MINERAI | self.MASQUE_ROCHE)
            noeud_col.setFromCollideMask(0)
            noeud.attachNewNode(noeud_col)

            self.liste_minerais.append({
                "node":            noeud,
                "type":            type_minerai["nom"],
                "pv":              3,            # 3 coups pour détruire
                "pos_base":        pos_base,
                "vibration_timer": 0.0,
                "vibration_phase": 0.0,
            })

    def on_clic_gauche(self):
        """Déclenché par mouse1 — tente de miner le minerai le plus proche."""
        # Capturer la souris si elle ne l'est pas encore
        if not self.souris_active:
            self.capturer_souris(True)
            return

        if self.timer_minage > 0:
            return   # cooldown actif

        pos_joueur = self.joueur_pivot.getPos()
        minerai_cible = None
        dist_min = self.distance_minage

        for m in self.liste_minerais:
            if m["pv"] <= 0:
                continue
            dist = (m["node"].getPos() - pos_joueur).length()
            if dist < dist_min:
                dist_min = dist
                minerai_cible = m

        if minerai_cible is None:
            # Rien à portée — feedback
            self.texte_action.setText("⛏  Trop loin d'un minerai !")
            self.taskMgr.doMethodLater(1.2, self.reset_texte_action, "reset_action")
            return

        # ---- COUP DE PIOCHE ----
        self.timer_minage = self.cooldown_minage
        minerai_cible["pv"] -= 1
        minerai_cible["vibration_timer"] = 0.35   # 350 ms de vibration
        minerai_cible["vibration_phase"] = 0.0

        if minerai_cible["pv"] <= 0:
            # Minerai détruit
            self.recolter_minerai(minerai_cible)
        else:
            pv_restants = minerai_cible["pv"]
            self.texte_action.setText(f"⛏  {pv_restants} coup(s) restant(s)…")
            self.taskMgr.doMethodLater(1.0, self.reset_texte_action, "reset_action")

    def recolter_minerai(self, m):
        """Supprime le nœud du minerai et met à jour l'inventaire."""
        nom = m["type"]
        self.inventaire[nom] += 1
        m["pv"] = 0
        m["node"].removeNode()
        self.texte_action.setText(f"✓  {nom.capitalize()} récolté !")
        self.taskMgr.doMethodLater(1.5, self.reset_texte_action, "reset_action")
        self.mettre_a_jour_hud_inventaire()

    def reset_texte_action(self, task):
        self.texte_action.setText("⛏  [Clic gauche] pour miner")
        return task.done

    def mettre_a_jour_hud_inventaire(self):
        e = self.inventaire["emeraude"]
        r = self.inventaire["rubis"]
        s = self.inventaire["saphir"]
        self.texte_minerais.setText(
            f" Émeraude *{e}    Rubis *{r}    Saphir *{s}"
        )

    #------------------------------------------
    #vibration des pierres
    #///////////////////////////////////
    def mettre_a_jour_vibrations(self, task):
        dt = globalClock.getDt()
        for m in self.liste_minerais:
            if m["vibration_timer"] > 0 and m["pv"] > 0:
                m["vibration_timer"] -= dt
                m["vibration_phase"] += dt * 40.0   # fréquence de tremblement
                amplitude = 0.12 * (m["vibration_timer"] / 0.35)
                decalage_x = math.sin(m["vibration_phase"] * math.pi) * amplitude
                decalage_z = abs(math.sin(m["vibration_phase"] * math.pi * 1.3)) * amplitude * 0.5
                pb = m["pos_base"]
                m["node"].setPos(pb.getX() + decalage_x, pb.getY(), pb.getZ() + decalage_z)
            elif m["pv"] > 0:
                # Remet en position de base quand la vibration est finie
                pb = m["pos_base"]
                m["node"].setPos(pb)
        return task.cont
#==============================================================================================


    # Configuration de la souris
    def capturer_souris(self, actif):
        self.souris_active = actif
        props = WindowProperties()
        props.setCursorHidden(actif)
        props.setMouseMode(
            WindowProperties.M_confined if actif
            else WindowProperties.M_absolute
        )
        self.win.requestProperties(props)
        
    def retour_menu(self):
        """Ferme le jeu et relance le menu CustomTkinter"""
        self.capturer_souris(False)
        import subprocess
        import sys
        subprocess.Popen([sys.executable, "interface.py"])
        self.userExit()

    def quitter_jeu(self):
        """Ferme complètement sans relancer le menu"""
        self.capturer_souris(False)
        self.userExit()


    def changer_touche(self, nom, etat):
        self.touches[nom] = etat


    #====================================================
    #placement des roches
    #====================================================
    def placer_roches_aleatoirement(self, nombre_roches):
        noms_roches = ["rock1", "rock2", "rock4", "rock5", "rock6","rock7","rock8","rock10","rock11","rock12","rock13","rock14","rock15","rock16"]

        self.zone_reservee_centre = (0, 0)
        self.zone_reservee_rayon  = 8

        limite_placement = 20

        
        #==============================================================
        #limitation au carte (ajustable)
        #==============================================================
        for i in range(nombre_roches):
        # Tirer une position valide (hors de la zone réservée)
            for _ in range(limite_placement):
                x = random.uniform(-limite_placement, limite_placement)
                y = random.uniform(-90, 90)
                dist = math.hypot(x - self.zone_reservee_centre[0],
                                y - self.zone_reservee_centre[1])
                if dist > self.zone_reservee_rayon:
                    break   # position valide trouvée

            nom = random.choice(noms_roches)
            scale = random.uniform(1.5, 3.5)
            rotation = random.uniform(0, 360)

            roche = self.loader.loadModel(f"models/rock/{nom}.glb")
            roche.reparentTo(self.render)
            roche.setPos(x, y, 0)
            roche.setScale(scale)
            roche.setH(rotation)

            #=======================================================
            #       reglage des collision pierre
            #=======================================================
            limites = roche.getTightBounds(roche)
            if limites:
                pmin, pmax = limites
                centre = (pmin + pmax) * 0.5
                rayon = (pmax - pmin).length() * 0.35
                if rayon <= 0:
                    rayon = 1.0
            else:
                centre = Point3(0, 0, 0)
                rayon = 1.0

            noeud_col_roche = CollisionNode(f"roche_col_{i}")
            noeud_col_roche.addSolid(
                CollisionSphere(centre.getX(), centre.getY(), centre.getZ(), rayon)
            )
            noeud_col_roche.setIntoCollideMask(self.MASQUE_ROCHE)
            noeud_col_roche.setFromCollideMask(0)  # la roche ne déclenche jamais de collision elle-même
            roche.attachNewNode(noeud_col_roche)


    #==========================================================
    #Faut pas y toucher
    #*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*
#==============================================================================
    def touche_mur(self, entry):
        if getattr(self, 'alerte_active', False):
            return
        self.alerte_active = True
        self.texte_alerte.setText("PAYEZ POUR DEBLOQUER!")
        self.taskMgr.doMethodLater(2.0, self.effacer_alerte, "effacer-alerte")

    def effacer_alerte(self, task):
        self.texte_alerte.setText("")
        self.alerte_active = False
        return task.done
#=============================================================================


    def mettre_a_jour_camera(self):
        yaw_rad   = math.radians(self.heading)
        pitch_rad = math.radians(self.pitch)

        px = self.joueur_pivot.getX() + self.cam_distance * math.sin(yaw_rad)   * math.cos(pitch_rad)
        py = self.joueur_pivot.getY() - self.cam_distance * math.cos(yaw_rad)   * math.cos(pitch_rad)
        pz = self.joueur_pivot.getZ() + self.cam_distance * math.sin(pitch_rad) + 1.0

        self.cam.setPos(px, py, pz)
        self.cam.lookAt(self.joueur_pivot.getX(),
                        self.joueur_pivot.getY(),
                        self.joueur_pivot.getZ() + 1.0)

    #========================================================
    #Besoin d'ajustement pour vue de haut
    #========================================================
    
    def basculer_vue(self):
        self.vue_haut = not self.vue_haut
        if self.vue_haut:
            # Vue de haut — caméra au-dessus qui regarde vers le bas
            x, y, z = self.joueur_pivot.getPos()
            self.cam.setPos(x, y, 90)     # hauteur 80 au-dessus
            self.cam.setHpr(0, -90, 0)    # regarde vers le bas
        else:
            # Retour vue normale 3e personne
            self.mettre_a_jour_camera()


    #==============================================
    #Activation souris pour tout autres (Pas touche sauf raison valable)
    #=============================================
    def mettre_a_jour(self, task):
        dt      = ClockObject.getGlobalClock().getDt()
        vitesse = 6.0

        #activation souris pour minage
        if self.timer_minage > 0:
            self.timer_minage -= dt

        if self.souris_active and self.mouseWatcherNode.hasMouse():
            md = self.win.getPointer(0)
            cx = self.win.getXSize() // 2
            cy = self.win.getYSize() // 2
            dx = md.getX() - cx
            dy = md.getY() - cy
            self.heading -= dx * 0.2
            self.pitch    = max(-10.0, min(60.0, self.pitch - dy * 0.2))
            self.win.movePointer(0, cx, cy)

        yaw_rad = math.radians(self.heading)

        dx, dy = 0.0, 0.0
        if self.touches["avant"]:
            dx -= math.sin(yaw_rad) * vitesse * dt
            dy += math.cos(yaw_rad) * vitesse * dt
        if self.touches["arriere"]:
            dx += math.sin(yaw_rad) * vitesse * dt
            dy -= math.cos(yaw_rad) * vitesse * dt
        if self.touches["gauche"]:
            dx -= math.cos(yaw_rad) * vitesse * dt
            dy -= math.sin(yaw_rad) * vitesse * dt
        if self.touches["droite"]:
            dx += math.cos(yaw_rad) * vitesse * dt
            dy += math.sin(yaw_rad) * vitesse * dt

        if dx != 0 or dy != 0:
            self.joueur_pivot.setX(self.joueur_pivot.getX() + dx)
            self.joueur_pivot.setY(self.joueur_pivot.getY() + dy)
            angle = math.degrees(math.atan2(dx, -dy))
            self.joueur_pivot.setH(angle)   
            
        #==================================================================
        #tjrs quelques erreur dans les pierres depassants (due par leur taille N)
        #==================================================================
        self.cTrav.traverse(self.render)
        if self.pnj_handler.getNumEntries() > 0:
            self.pnj_handler.sortEntries()
            pt = self.pnj_handler.getEntry(0).getSurfacePoint(self.render)
            self.z_pnj = pt.getZ()
        self.pnj.setZ(self.z_pnj + 1.0)
        # Mouvement aléatoire de Ralph
        self.pnj_timer -= dt
        if self.pnj_timer <= 0:
            self.pnj_direction = random.uniform(0, 360)
            self.pnj_timer     = self.pnj_interval

        rad = math.radians(self.pnj_direction)
        self.pnj.setX(self.pnj.getX() + math.sin(rad) * self.pnj_vitesse * dt)
        self.pnj.setY(self.pnj.getY() - math.cos(rad) * self.pnj_vitesse * dt)
        self.pnj.setH(self.pnj_direction)   # tourne Ralph dans la direction de marche

        if self.sol_handler.getNumEntries() > 0:
            self.sol_handler.sortEntries()
            point_sol = self.sol_handler.getEntry(0).getSurfacePoint(self.render)
            self.z_sol_actuel = point_sol.getZ()

        self.joueur_pivot.setZ(self.z_sol_actuel + self.hauteur_joueur)

        # Remplace la ligne self.mettre_a_jour_camera() par :
        if not self.vue_haut:
            # Le fond suit toujours le joueur en X/Y pour un effet d'horizon infini
            self.noeud_fond.setPos(self.joueur_pivot.getX(), self.joueur_pivot.getY() + 300, -20)
            self.mettre_a_jour_camera()



        x, y, z = self.joueur_pivot.getPos()
        self.texte_pos.setText(f"X={x:.1f}  Y={y:.1f}  Z={z:.1f}")

        

        return task.cont


if __name__ == "__main__":
    app = BoutiquePierres()
    app.run()