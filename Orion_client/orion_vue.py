# -*- coding: utf-8 -*-
##  version 2022 14 mars - jmd

from tkinter import *
from tkinter import ttk, PhotoImage
from tkinter.simpledialog import *
from tkinter.messagebox import *
from helper import Helper as hlp
import math
import os.path

import random


class Vue():
    def __init__(self, parent, urlserveur, mon_nom, msg_initial):
        self.minutes = 10
        self.secondes = 00
        self.parent = parent
        self.root = Tk()
        self.root.title("Je suis " + mon_nom)
        self.mon_nom = mon_nom
        # attributs
        self.taille_minimap = 240 # 240 quoi?
        self.zoom = 2
        self.ma_selection = None
        self.cadre_actif = None
        self.nbrPoints = 100
        self.nbrMetal = 0
        self.nbrEnergie = 0
        self.nbrPopulation = 0
        # cadre principal de l'application
        self.cadre_app = Frame(self.root, width=500, height=400, bg="red")
        self.cadre_app.pack(expand=1, fill=BOTH)
        # # un dictionnaire pour conserver les divers cadres du jeu, creer plus bas
        self.cadres = {}
        self.creer_cadres(urlserveur, mon_nom, msg_initial)
        self.changer_cadre("splash")
        # PROTOCOLE POUR INTERCEPTER LA FERMETURE DU ROOT - qui termine l'application
        # self.root.protocol("WM_DELETE_WINDOW", self.demander_abandon)
        
        # affichage/images
        dossier_images = os.path.join(os.path.curdir, 'images')
        self.imageEtoile = PhotoImage(file=os.path.join(dossier_images, 'star.png')).subsample(6,6)
        self.imageVaissExplo = PhotoImage(file=os.path.join(dossier_images, 'vaisseauExploration.png')).subsample(6,6)
        # self.imageVaissExtra = PhotoImage(file=os.path.join(dossier_images, 'vaisseauExtra.png')).subsample(6, 6)

        # # sera charge apres l'initialisation de la partie, contient les donnees pour mettre l'interface a jour
        self.modele = None
        # # variable pour suivre le trace du multiselect
        self.debut_selection = []
        self.selecteur_actif = None

    def demander_abandon(self):
        rep = askokcancel("Vous voulez vraiment quitter?")
        if rep:
            self.root.after(500, self.root.destroy)

    ####### INTERFACES GRAPHIQUES
    def changer_cadre(self, nomcadre):
        cadre = self.cadres[nomcadre]
        if self.cadre_actif:
            self.cadre_actif.pack_forget()
        self.cadre_actif = cadre
        self.cadre_actif.pack(expand=1, fill=BOTH)

    ###### LES CADRES ############################################################################################
    def creer_cadres(self, urlserveur, mon_nom, msg_initial):
        self.cadres["splash"] = self.creer_cadre_splash(urlserveur, mon_nom, msg_initial)
        self.cadres["lobby"] = self.creer_cadre_lobby()
        self.cadres["partie"] = self.creer_cadre_partie()

    # le splash (ce qui 'splash' ?? l'??cran lors du d??marrage)
    # sera le cadre visuel initial lors du lancement de l'application
    def creer_cadre_splash(self, urlserveur, mon_nom, msg_initial):
        self.cadre_splash = Frame(self.cadre_app)
        # un canvas est utilis?? pour 'dessiner' les widgets de cette fen??tre voir 'create_window' plus bas
        self.canevas_splash = Canvas(self.cadre_splash, width=600, height=480, bg="gray20")
        self.canevas_splash.pack()

        # creation ds divers widgets (champ de texte 'Entry' et boutons cliquables (Button)
        self.etatdujeu = Label(text=msg_initial, font=("Arial", 18), borderwidth=2, relief=RIDGE)
        self.nomsplash = Entry(font=("Arial", 14))
        self.urlsplash = Entry(font=("Arial", 14), width=42)
        self.btnurlconnect = Button(text="Connecter", font=("Arial", 12), command=self.connecter_serveur)
        # on ins??re les infos par d??faut (nom url) et re??u au d??marrage (dispo)
        self.nomsplash.insert(0, mon_nom)
        self.urlsplash.insert(0, urlserveur)
        # on les place sur le canevas_splash
        self.canevas_splash.create_window(320, 100, window=self.etatdujeu, width=400, height=30)
        self.canevas_splash.create_window(320, 200, window=self.nomsplash, width=400, height=30)
        self.canevas_splash.create_window(210, 250, window=self.urlsplash, width=360, height=30)
        self.canevas_splash.create_window(480, 250, window=self.btnurlconnect, width=100, height=30)
        # les boutons d'actions
        self.btncreerpartie = Button(text="Creer partie", font=("Arial", 12), state=DISABLED, command=self.creer_partie)
        self.btninscrirejoueur = Button(text="Inscrire joueur", font=("Arial", 12), state=DISABLED,
                                        command=self.inscrire_joueur)
        self.btnreset = Button(text="Reinitialiser partie", font=("Arial", 9), state=DISABLED,
                               command=self.reset_partie)

        # on place les autres boutons
        self.canevas_splash.create_window(420, 350, window=self.btncreerpartie, width=200, height=30)
        self.canevas_splash.create_window(420, 400, window=self.btninscrirejoueur, width=200, height=30)
        self.canevas_splash.create_window(420, 450, window=self.btnreset, width=200, height=30)

        # on retourne ce cadre pour l'ins??rer dans le dictionnaires des cadres
        return self.cadre_splash

    ######## le lobby (o?? on attend les inscriptions)
    def creer_cadre_lobby(self):
        # le cadre lobby, pour isncription des autres joueurs, remplace le splash
        self.cadrelobby = Frame(self.cadre_app)
        self.canevaslobby = Canvas(self.cadrelobby, width=640, height=480, bg="gray20")
        self.canevaslobby.pack()
        # widgets du lobby
        # un listbox pour afficher les joueurs inscrit pour la partie ?? lancer
        self.listelobby = Listbox(borderwidth=2, relief=GROOVE)
        
        #timer
        self.liste_options_temps = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
        self.options_temps = ttk.Combobox(values=self.liste_options_temps, state="normal")
        self.options_temps.current(0)
        self.options_temps.bind("<<ComboboxSelected>>", self.update_timer)
        self.label_temps = Label(text="Dur??e de la partie en minutes :")

        # bouton pour lancer la partie, uniquement accessible ?? celui qui a creer la partie dans le splash
        self.btnlancerpartie = Button(text="Lancer partie", state=DISABLED, command=self.lancer_partie)
        # affichage des widgets dans le canevaslobby (similaire au splash)
        self.canevaslobby.create_window(440, 240, window=self.listelobby, width=200, height=400)
        self.canevaslobby.create_window(200, 400, window=self.btnlancerpartie, width=100, height=30)
        self.canevaslobby.create_window(200, 200, window=self.options_temps, width=100, height=30)
        self.canevaslobby.create_window(200, 170, window=self.label_temps, width=200, height=30)
        # on retourne ce cadre pour l'ins??rer dans le dictionnaires des cadres
        return self.cadrelobby
    
    def update_timer(self, event):
        self.minutes = int(self.options_temps.get())
        print(self.minutes)

    def creer_cadre_partie(self):
        self.cadrepartie = Frame(self.cadre_app, width=600, height=200, bg="yellow")
        self.cadrejeu = Frame(self.cadrepartie, width=600, height=200, bg="teal")

        self.scrollX = Scrollbar(self.cadrejeu, orient=HORIZONTAL)
        self.scrollY = Scrollbar(self.cadrejeu, orient=VERTICAL)
        self.canevas = Canvas(self.cadrejeu, width=800, height=600,
                              xscrollcommand=self.scrollX.set,
                              yscrollcommand=self.scrollY.set, bg="grey11")

        self.scrollX.config(command=self.canevas.xview)
        self.scrollY.config(command=self.canevas.yview)

        self.canevas.grid(column=0, row=0, sticky=W + E + N + S)
        self.scrollX.grid(column=0, row=1, sticky=W + E)
        self.scrollY.grid(column=1, row=0, sticky=N + S)

        self.cadrejeu.columnconfigure(0, weight=1)
        self.cadrejeu.rowconfigure(0, weight=1)
        self.canevas.bind("<Button>", self.cliquer_cosmos)
        self.canevas.tag_bind(ALL, "<Button>", self.cliquer_cosmos)

        # faire une multiselection
        self.canevas.bind("<Shift-Button-1>", self.debuter_multiselection)
        self.canevas.bind("<Shift-B1-Motion>", self.afficher_multiselection)
        self.canevas.bind("<Shift-ButtonRelease-1>", self.terminer_multiselection)

        # scroll avec roulette
        self.canevas.bind("<MouseWheel>", self.defiler_vertical)
        self.canevas.bind("<Control-MouseWheel>", self.defiler_horizon)

        self.creer_cadre_outils()

        self.cadrejeu.pack(side=LEFT, expand=1, fill=BOTH)
        self.label_points = Label(self.cadreoutils, text="Points : " + str(self.nbrPoints))
        self.label_metal = Label(self.cadreoutils, text="M??tal : " + str(self.nbrMetal))
        self.label_energie = Label(self.cadreoutils, text="??nergie : " + str(self.nbrEnergie))
        self.label_population = Label(self.cadreoutils, text="Population : " + str(self.nbrPopulation))
        self.label_points.pack(side=TOP)
        self.label_metal.pack(side=TOP)
        self.label_energie.pack(side=TOP)
        self.label_population.pack(side=TOP)
        return self.cadrepartie
    
    def update_cadre_timer(self):
        self.cadre_timer.config(text=(str(self.minutes) + ":" + str(self.secondes)))

    def creer_cadre_outils(self):
        self.cadreoutils = Frame(self.cadrepartie, width=200, height=200, bg="darkgrey")
        self.cadreoutils.pack(side=LEFT, fill=Y)

        self.cadreinfo = Frame(self.cadreoutils, width=200, height=200, bg="darkgrey")
        self.cadreinfo.pack(fill=BOTH)

        self.cadreinfogen = Frame(self.cadreinfo, width=200, height=200, bg="grey50")
        self.cadreinfogen.pack(fill=BOTH)
        self.labid = Label(self.cadreinfogen, text="Inconnu")
        self.labid.bind("<Button>", self.centrer_planemetemere)
        self.labid.pack()
        self.btnmini = Button(self.cadreinfogen, text="MINI")
        self.btnmini.bind("<Button>", self.afficher_mini)
        self.btnmini.pack()

        self.cadreinfochoix = Frame(self.cadreinfo, height=200, width=200, bg="grey30")
        self.btncreervaisseau = Button(self.cadreinfochoix, text="Vaisseau")
        self.btncreervaisseau.bind("<Button>", self.creer_vaisseau)
        self.btncreercargo = Button(self.cadreinfochoix, text="Cargo")
        self.btncreercargo.bind("<Button>", self.creer_vaisseau)

        self.btncreervaisseau.pack()
        self.btncreercargo.pack()

        self.cadreinfoliste = Frame(self.cadreinfo)

        self.scroll_liste_Y = Scrollbar(self.cadreinfoliste, orient=VERTICAL)
        self.info_liste = Listbox(self.cadreinfoliste, width=20, height=6, yscrollcommand=self.scroll_liste_Y.set)
        self.info_liste.bind("<Button-3>", self.centrer_liste_objet)
        self.info_liste.grid(column=0, row=0, sticky=W + E + N + S)
        self.scroll_liste_Y.grid(column=1, row=0, sticky=N + S)

        self.cadreinfoliste.columnconfigure(0, weight=1)
        self.cadreinfoliste.rowconfigure(0, weight=1)

        self.cadreinfoliste.pack(side=BOTTOM, expand=1, fill=BOTH)

        self.cadreminimap = Frame(self.cadreoutils, height=200, width=200, bg="black")
        self.canevas_minimap = Canvas(self.cadreminimap, width=self.taille_minimap, height=self.taille_minimap,
                                      bg="gray85")
        self.canevas_minimap.bind("<Button>", self.positionner_minicanevas)
        self.canevas_minimap.pack()
        self.cadreminimap.pack(side=BOTTOM)
        
        #cadre action etoile
        self.cadre_actions_etoile = Frame(self.cadreinfo, height=200, width=200, bg="grey30")
        self.btn_scanner = Button(self.cadre_actions_etoile, text="Scanner")
        self.btn_coloniser = Button(self.cadre_actions_etoile, text="Coloniser")
        #self.btn_scanner.pack()

        # cadre info etoile
        self.cadre_info_etoile = Frame(self.cadreinfo, height=300, width=300, bg="grey30")
        self.champ_metal = Label(self.cadre_info_etoile)
        self.champ_energie = Label(self.cadre_info_etoile)
        self.champ_population = Label(self.cadre_info_etoile)
        self.champ_metal.pack()
        self.champ_energie.pack()
        self.champ_population.pack()

        #timer
        self.cadre_timer = Label(self.cadreoutils, text=(str(self.minutes) + ":" + str(self.secondes)), width=4, height=1, bg="pink")
        self.cadre_timer.pack(side=BOTTOM)

        self.cadres["jeu"] = self.cadrepartie
        # fonction qui affiche le nombre d'items sur le jeu
        self.canevas.bind("<Shift-Button-3>", self.calc_objets)
        
    def afficher_ressources(self, evt, id):
        i = 0
        for etoile in self.modele.etoiles:
            if etoile.id == id:
                break
            else:
                i += 1
        self.champ_metal.config(text=("Metal : " + str(self.modele.etoiles[i].ressources["metal"])))
        self.champ_energie.config(text=("Energie : " + str(self.modele.etoiles[i].ressources["energie"])))
        self.champ_population.config(text=("Population : " + str(self.modele.etoiles[i].ressources["population"])))
        self.cadre_info_etoile.pack()

    def coloniser(self, evt, id):
        i = 0
        for etoile in self.modele.etoiles:
            if etoile.id == id:
                break
            else:
                i += 1
        self.nbrMetal += self.modele.etoiles[i].ressources["metal"]
        self.nbrEnergie += self.modele.etoiles[i].ressources["energie"]
        self.nbrPopulation += self.modele.etoiles[i].ressources["population"]
        self.nbrPoints += 15
        self.label_points.config(text=("Points : " + str(self.nbrPoints)))
        self.label_metal.config(text=("Metal : " + str(self.nbrMetal)))
        self.label_energie.config(text=("Energie : " + str(self.nbrEnergie)))
        self.label_existentielle.config(text=("Population : " + str(self.nbrPopulation)))
        # self.btn_coloniser.config(state=DISABLED)
        self.btn_coloniser.pack_forget()

    def connecter_serveur(self):
        self.btninscrirejoueur.config(state=NORMAL)
        self.btncreerpartie.config(state=NORMAL)
        self.btnreset.config(state=NORMAL)
        url_serveur = self.urlsplash.get()
        self.parent.connecter_serveur(url_serveur)

    def centrer_liste_objet(self, evt):
        info = self.info_liste.get(self.info_liste.curselection())
        print(info)
        liste_separee = info.split(";")
        type_vaisseau = liste_separee[0]
        id = liste_separee[1][1:]
        obj = self.modele.joueurs[self.mon_nom].flotte[type_vaisseau][id]
        self.centrer_objet(obj)

    def calc_objets(self, evt):
        print("Univers = ", len(self.canevas.find_all()))

    def defiler_vertical(self, evt):
        rep = self.scrollY.get()[0]
        if evt.delta < 0:
            rep = rep + 0.01
        else:
            rep = rep - 0.01
        self.canevas.yview_moveto(rep)

    def defiler_horizon(self, evt):
        rep = self.scrollX.get()[0]
        if evt.delta < 0:
            rep = rep + 0.02
        else:
            rep = rep - 0.02
        self.canevas.xview_moveto(rep)

    ##### FONCTIONS DU SPLASH #########################################################################

    ###  FONCTIONS POUR SPLASH ET LOBBY INSCRIPTION pour participer a une partie
    def update_splash(self, etat):
        if "attente" in etat or "courante" in etat:
            self.btncreerpartie.config(state=DISABLED)
        if "courante" in etat:
            self.etatdujeu.config(text="Desole - partie encours !")
            self.btninscrirejoueur.config(state=DISABLED)
        elif "attente" in etat:
            self.etatdujeu.config(text="Partie en attente de joueurs !")
            self.btninscrirejoueur.config(state=NORMAL)
        elif "dispo" in etat:
            self.etatdujeu.config(text="Bienvenue ! Serveur disponible")
            self.btninscrirejoueur.config(state=DISABLED)
            self.btncreerpartie.config(state=NORMAL)
        else:
            self.etatdujeu.config(text="ERREUR - un probleme est survenu")

    def reset_partie(self):
        rep = self.parent.reset_partie()

    def creer_partie(self):
        nom = self.nomsplash.get()
        self.parent.creer_partie(nom)

    ##### FONCTION DU LOBBY #############
    def update_lobby(self, dico):
        self.listelobby.delete(0, END)
        for i in dico:
            self.listelobby.insert(END, i[0])
        if self.parent.joueur_createur:
            self.btnlancerpartie.config(state=NORMAL)

    def inscrire_joueur(self):
        nom = self.nomsplash.get()
        urljeu = self.urlsplash.get()
        self.parent.inscrire_joueur(nom, urljeu)

    def lancer_partie(self):
        self.parent.lancer_partie()

    def initialiser_avec_modele(self, modele):
        self.mon_nom = self.parent.mon_nom
        self.modele = modele
        self.canevas.config(scrollregion=(0, 0, modele.largeur, modele.hauteur))

        self.labid.config(text=self.mon_nom)
        self.labid.config(fg=self.modele.joueurs[self.mon_nom].couleur)

        self.afficher_decor(modele)

    ####################################################################################################

    def positionner_minicanevas(self, evt):
        x = evt.x
        y = evt.y

        pctx = x / self.taille_minimap
        pcty = y / self.taille_minimap

        xl = (self.canevas.winfo_width() / 2) / self.modele.largeur
        yl = (self.canevas.winfo_height() / 2) / self.modele.hauteur

        self.canevas.xview_moveto(pctx - xl)
        self.canevas.yview_moveto(pcty - yl)
        xl = self.canevas.winfo_width()
        yl = self.canevas.winfo_height()

    def afficher_decor(self, mod):
        # on cree un arriere fond de petites etoieles NPC pour le look
        for i in range(len(mod.etoiles) * 50):
            x = random.randrange(int(mod.largeur))
            y = random.randrange(int(mod.hauteur))
            n = random.randrange(3) + 1
            col = random.choice(["LightYellow", "azure1", "pink"])
            self.canevas.create_oval(x, y, x + n, y + n, fill=col, tags=("fond",))
        # affichage des etoiles
        for i in mod.etoiles:
            t = i.taille * self.zoom
            imageEtoile = self.canevas.create_image(i.x, i.y, anchor=NW, image=self.imageEtoile)
            self.canevas.itemconfig(imageEtoile)
            # cercle vide large
            # self.canevas.create_oval(i.x - t + 2, i.y - t + 2, i.x + t - 2, i.y + t - 2,
            #                          fill='', outline=col, width=4,
            #                          tags=(i.proprietaire, str(i.id), "Etoile",))
            # cercle plein petit
            self.canevas.create_oval(i.x + t, i.y + t, i.x - t, i.y - t,
                                     fill=col, outline=col, width=4,
                                     tags=(i.proprietaire, str(i.id), "Etoile",))

            # recuperer dimensions image
            imageEtoile_width = self.imageEtoile.width()
            imageEtoile_height = self.imageEtoile.height()

            # centrer image
            image_x = i.x - imageEtoile_width / 2
            image_y = i.y - imageEtoile_height / 2

            # positioner image au centre
            self.canevas.coords(imageEtoile, image_x, image_y)

        # affichage des etoiles possedees par les joueurs
        for i in mod.joueurs.keys():
            for j in mod.joueurs[i].etoilescontrolees:
                t = j.taille * self.zoom
                self.canevas.create_oval(j.x - t, j.y - t, j.x + t, j.y + t,
                                         fill=mod.joueurs[i].couleur,
                                         tags=(j.proprietaire, str(j.id), "Etoile"))
                # on affiche dans minimap
                minix = j.x / self.modele.largeur * self.taille_minimap
                miniy = j.y / self.modele.hauteur * self.taille_minimap
                self.canevas_minimap.create_rectangle(minix, miniy, minix + 3, miniy + 3,
                                                      fill=mod.joueurs[i].couleur,
                                                      tags=(j.proprietaire, str(j.id), "Etoile"))

    def afficher_mini(self, evt):  # univers(self, mod):
        self.canevas_minimap.delete("mini")
        for j in self.modele.etoiles:
            minix = j.x / self.modele.largeur * self.taille_minimap
            miniy = j.y / self.modele.hauteur * self.taille_minimap
            self.canevas_minimap.create_rectangle(minix, miniy, minix + 0, miniy + 0,
                                                  fill="black",
                                                  tags=("mini", "Etoile"))
        # # affichage des etoiles possedees par les joueurs
        # for i in mod.joueurs.keys():
        #     for j in mod.joueurs[i].etoilescontrolees:
        #         t = j.taille * self.zoom
        #         self.canevas.create_oval(j.x - t, j.y - t, j.x + t, j.y + t,
        #                                  fill=mod.joueurs[i].couleur,
        #                                  tags=(j.proprietaire, str(j.id),  "Etoile"))

    def centrer_planemetemere(self, evt):
        self.centrer_objet(self.modele.joueurs[self.mon_nom].etoilemere)

    def centrer_objet(self, objet):
        # permet de defiler l'??cran jusqu'?? cet objet
        x = objet.x
        y = objet.y

        x1 = self.canevas.winfo_width() / 2
        y1 = self.canevas.winfo_height() / 2

        pctx = (x - x1) / self.modele.largeur
        pcty = (y - y1) / self.modele.hauteur

        self.canevas.xview_moveto(pctx)
        self.canevas.yview_moveto(pcty)

    # change l'appartenance d'une etoile et donc les propri??t??s des dessins les repr??sentants
    def afficher_etoile(self, joueur, cible):
        joueur1 = self.modele.joueurs[joueur]
        id = cible.id
        couleur = joueur1.couleur
        self.canevas.itemconfig(id, fill=couleur)
        self.canevas.itemconfig(id, tags=(joueur, id, "Etoile",))

    # ajuster la liste des vaisseaux
    def lister_objet(self, obj, id):
        self.info_liste.insert(END, obj + "; " + id)

    def creer_vaisseau(self, evt):
        type_vaisseau = evt.widget.cget("text")
        self.parent.creer_vaisseau(type_vaisseau)
        self.ma_selection = None
        self.canevas.delete("marqueur")
        self.cadreinfochoix.pack_forget()

    def afficher_jeu(self):
        mod = self.modele
        self.canevas.delete("artefact")
        self.canevas.delete("objet_spatial")

        if self.ma_selection != None:
            joueur = mod.joueurs[self.ma_selection[0]]
            if self.ma_selection[2] == "Etoile":
                for i in joueur.etoilescontrolees:
                    if i.id == self.ma_selection[1]:
                        x = i.x
                        y = i.y
                        t = 10 * self.zoom
                        self.canevas.create_oval(x - t, y - t, x + t, y + t,
                                                 dash=(2, 2), outline=mod.joueurs[self.mon_nom].couleur,
                                                 tags=("multiselection", "marqueur"))
            elif self.ma_selection[2] == "Vaisseau" or self.ma_selection[2] == "Cargo":
                for j in joueur.flotte:
                    for i in joueur.flotte[j]:
                        i = joueur.flotte[j][i]
                        if i.id == self.ma_selection[1]:
                            x = i.x
                            y = i.y
                            t = 10 * self.zoom
                            self.canevas.create_rectangle(x - t, y - t, x + t, y + t,
                                                          dash=(2, 2), outline=mod.joueurs[self.mon_nom].couleur,
                                                          tags=("multiselection", "marqueur"))
        # afficher asset des joueurs
        for i in mod.joueurs.keys():
            i = mod.joueurs[i]
            vaisseau_local = []
            for k in i.flotte:
                for j in i.flotte[k]:
                    j = i.flotte[k][j]
                    tailleF = j.taille * self.zoom
                    if k == "Vaisseau":
                        self.canevas.create_rectangle((j.x - tailleF), (j.y - tailleF),
                                                      (j.x + tailleF), (j.y + tailleF), fill=i.couleur,
                                                      tags=(j.proprietaire, str(j.id), "Vaisseau", k, "artefact"))
                    elif k == "Cargo":
                        # self.dessiner_cargo(j,tailleF,i,k)
                        self.dessiner_cargo(j, tailleF, i, k)
                        # self.canevas.create_oval((j.x - tailleF), (j.y - tailleF),
                        #                          (j.x + tailleF), (j.y + tailleF), fill=i.couleur,
                        #                          tags=(j.proprietaire, str(j.id), "Flotte",k,"artefact"))
        for t in self.modele.trou_de_vers:
            i = t.porte_a
            for i in [t.porte_a, t.porte_b]:
                self.canevas.create_oval(i.x - i.pulse, i.y - i.pulse,
                                         i.x + i.pulse, i.y + i.pulse, outline=i.couleur, width=2, fill="grey15",
                                         tags=("", i.id, "Porte_de_ver", "objet_spatial"))

                self.canevas.create_oval(i.x - i.pulse, i.y - i.pulse,
                                         i.x + i.pulse, i.y + i.pulse, outline=i.couleur, width=2, fill="grey15",
                                         tags=("", i.id, "Porte_de_ver", "objet_spatial"))

    def dessiner_cargo(self, obj, tailleF, joueur, type_obj):
        t = obj.taille * self.zoom
        a = obj.ang
        x, y = hlp.getAngledPoint(obj.angle_cible, int(t / 4 * 3), obj.x, obj.y)
        dt = t / 2
        self.canevas.create_oval((obj.x - tailleF), (obj.y - tailleF),
                                 (obj.x + tailleF), (obj.y + tailleF), fill=joueur.couleur,
                                 tags=(obj.proprietaire, str(obj.id), "Cargo", type_obj, "artefact"))
        self.canevas.create_oval((x - dt), (y - dt),
                                 (x + dt), (y + dt), fill="yellow",
                                 tags=(obj.proprietaire, str(obj.id), "Cargo", type_obj, "artefact"))

    def dessiner_cargo1(self, j, tailleF, i, k):
        self.canevas.create_oval((j.x - tailleF), (j.y - tailleF),
                                 (j.x + tailleF), (j.y + tailleF), fill=i.couleur,
                                 tags=(j.proprietaire, str(j.id), "Cargo", k, "artefact"))

    def cliquer_cosmos(self, evt):
        t = self.canevas.gettags(CURRENT)
        self.cadre_actions_etoile.pack_forget()
        self.cadreinfochoix.pack_forget()
        self.cadre_info_etoile.pack_forget()

        if t:  # il y a des tags
            if t[0] == "" and t[2] == "Etoile":
                self.btn_scanner.config(command=lambda: self.afficher_ressources(evt, t[1]))
                self.btn_coloniser.config(command=lambda: self.coloniser(evt, t[1]))
                self.montrer_actions_etoile()
                
                if self.ma_selection != None:    
                    if self.ma_selection[2] == "Cargo":
                        self.btn_coloniser.pack()
                        self.btn_scanner.pack_forget()
                        # self.btn_coloniser.config(command=self.forget_button)
                        # self.messageArrivee = Label(self.cadreoutils, text="??toile colonis??e!")
                        # self.cadreoutils.after(2000, self.messageArrivee.pack())
                        print("cargo")

            if self.ma_selection != None:
                if self.ma_selection[2] == "Vaisseau":
                    self.btn_coloniser.pack_forget()
                    self.btn_scanner.pack()


            if t[0] == self.mon_nom:  # et
                self.ma_selection = [self.mon_nom, t[1], t[2]]
                if t[2] == "Etoile":
                    self.montrer_etoile_selection()
                elif t[2] == "Cargo" or t[2] == "Vaisseau":
                    self.montrer_flotte_selection()
            elif ("Etoile" in t or "Porte_de_ver" in t) and t[0] != self.mon_nom:
                if self.ma_selection:
                    self.parent.cibler_flotte(self.ma_selection[1], t[1], t[2])
                self.ma_selection = None
                self.canevas.delete("marqueur")
                
        else:  # si on n'a pas choisi une etoile (on veut se deplacer vers l'espace)
            #interface
            print("Region inconnue")
            self.btn_coloniser.pack_forget()
            self.btn_scanner.pack_forget()

            #deplacement dans le vide
            if self.ma_selection != None:
                if self.ma_selection[2] == "Vaisseau" or self.ma_selection[2] == "Cargo":  # si on a deja choisi un vaiseau pour avoir un point de depart
                    positionDestinationX = self.canevas.canvasx(evt.x)
                    positionDestinationY = self.canevas.canvasy(evt.y)
                    print(f'X: {positionDestinationX}')
                    print(f'Y: {positionDestinationY}')

                    self.parent.cibler_flotte_espace(self.ma_selection[1], positionDestinationX, positionDestinationY,
                                                     "espace")
                    self.canevas.delete("marqueur")
                    self.ma_selection = None
                else:
                    print("Vous devez choisir un point d'origine")
                    self.ma_selection = None

    def montrer_etoile_selection(self):
        self.cadreinfochoix.pack(fill=BOTH)

    def montrer_actions_etoile(self):
        self.cadre_actions_etoile.pack(fill=BOTH)

    def montrer_flotte_selection(self):
        print("?? IMPLANTER - FLOTTE de ", self.mon_nom)

    # Methodes pour multiselect#########################################################
    def debuter_multiselection(self, evt):
        self.debutselect = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
        x1, y1 = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
        self.selecteur_actif = self.canevas.create_rectangle(x1, y1, x1 + 1, y1 + 1, outline="red", width=2,
                                                             dash=(2, 2), tags=("", "selecteur", "", ""))

    def afficher_multiselection(self, evt):
        if self.debutselect:
            x1, y1 = self.debutselect
            x2, y2 = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
            self.canevas.coords(self.selecteur_actif, x1, y1, x2, y2)

    def terminer_multiselection(self, evt):
        if self.debutselect:
            x1, y1 = self.debutselect
            x2, y2 = (self.canevas.canvasx(evt.x), self.canevas.canvasy(evt.y))
            self.debutselect = []
            objchoisi = (list(self.canevas.find_enclosed(x1, y1, x2, y2)))
            for i in objchoisi:
                if self.parent.mon_nom not in self.canevas.gettags(i):
                    objchoisi.remove(i)
                else:
                    self.objets_selectionnes.append(self.canevas.gettags(i)[2])

            self.canevas.delete("selecteur")

    ### FIN du multiselect
