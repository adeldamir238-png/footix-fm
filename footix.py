import json, os, re, threading, time
import urllib.parse
from flask import Flask, redirect, request
import requests

app = Flask(__name__)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "").strip()


class JoueurFM:

  def __init__(self):
    self.nom = "Léo Mercier"
    self.poste = "Milieu Relayeur"
    self.age = 15
    self.categorie = "U17 Nationaux"
    self.xp = 0
    self.condition = 95
    self.moral = "Confiant"
    self.esprit_critique = 10
    self.technique = 9.5
    self.mental = 10.0
    self.physique = 9.0
    self.atelier = "Toros & Vision du jeu"
    self.pensee = "J'arrive au centre de formation, prêt à progresser !"
    self.dernier_evenement = "Entrée au centre de formation."
    self.info_mentor = ""
    self.reponse_mentor = "En attente de tes conseils ou analyses, Coach !"
    self.equipe_5 = "Donnarumma, Zabarnyi, Vitinha, Zaïre-Emery, Dembélé"
    self.bilan_equipe = "En attente de l'analyse de tes 5 joueurs modèles..."
    self.predictions = []
    self.charger()

  def note_globale(self):
    return round((self.technique + self.mental + self.physique) / 3.0, 1)

  def charger(self):
    if not SUPABASE_URL or not SUPABASE_KEY:
      return
    try:
      r = requests.get(
          f"{SUPABASE_URL}/rest/v1/joueur_fm?id=eq.1&select=*",
          headers={
              "apikey": SUPABASE_KEY,
              "Authorization": f"Bearer {SUPABASE_KEY}",
          },
          timeout=10,
      )
      if r.status_code == 200 and r.json():
        e = next(iter(r.json()))
        self.nom = e.get("nom", self.nom)
        self.poste = e.get("poste", self.poste)
        self.age = int(e.get("age", 15))
        self.categorie = e.get("categorie", self.categorie)
        self.xp = int(e.get("xp", 0))
        self.condition = int(e.get("condition", 95))
        self.moral = e.get("moral", "Confiant")
        self.esprit_critique = int(e.get("esprit_critique", 10))
        self.technique = float(e.get("technique", 9.5))
        self.mental = float(e.get("mental", 10.0))
        self.physique = float(e.get("physique", 9.0))
        self.atelier = e.get("atelier", self.atelier)
        self.pensee = e.get("pensee", self.pensee)
        self.dernier_evenement = e.get(
            "dernier_evenement", self.dernier_evenement
        )
        if e.get("reponse_mentor"):
          self.reponse_mentor = e["reponse_mentor"]
        if e.get("equipe_5"):
          self.equipe_5 = e["equipe_5"]
        if e.get("bilan_equipe"):
          self.bilan_equipe = e["bilan_equipe"]
        if e.get("predictions_json"):
          self.predictions = json.loads(e["predictions_json"])
          
    except Exception:
      pass

  def sauvegarder(self):
    if not SUPABASE_URL or not SUPABASE_KEY:
      return
    try:
      url = f"{SUPABASE_URL}/rest/v1/joueur_fm"
      headers = {
          "apikey": SUPABASE_KEY,
          "Authorization": f"Bearer {SUPABASE_KEY}",
          "Content-Type": "application/json",
          "Prefer": "resolution=merge-duplicates",
      }
      payload = {
          "id": 1,
          "nom": self.nom,
          "poste": self.poste,
          "age": self.age,
          "categorie": self.categorie,
          "xp": self.xp,
          "condition": self.condition,
          "moral": self.moral,
          "esprit_critique": self.esprit_critique,
          "technique": round(self.technique, 2),
          "mental": round(self.mental, 2),
          "physique": round(self.physique, 2),
          "atelier": self.atelier,
          "pensee": self.pensee,
          "dernier_evenement": self.dernier_evenement,
          "info_mentor": self.info_mentor,
          "reponse_mentor": self.reponse_mentor,
          "equipe_5": self.equipe_5,
          "bilan_equipe": self.bilan_equipe,
      }
      requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception:
      pass

  def lire_actualite_foot(self):
    infos = []
    # 1. Recherche des performances récentes des 5 joueurs choisis (façon Sorare)
    joueurs_liste = [j.strip() for j in self.equipe_5.split(",") if j.strip()][:5]
    for j in joueurs_liste:
      try:
        q = urllib.parse.quote(f"{j} note match performance football")
        url_j = "".join([
            "https://news.google",
            f".com/rss/search?q={q}&hl=fr&gl=FR&ceid=FR:fr",
        ])
        rss_j = requests.get(url_j, timeout=5).text
        titres_j = re.findall(r"<title>(.*?)</title>", rss_j)[1:3]
        if titres_j:
          infos.append(f"Actu {j} : " + " / ".join(titres_j))
      except Exception:
        pass

    # 2. Vérification de l'info ou intox du Coach
    if self.info_mentor:
      try:
        mots_cles = " ".join(
            [m for m in self.info_mentor.split() if len(m) > 3][:4]
        )
        requete = urllib.parse.quote(mots_cles + " football")
        url_verif = "".join([
            "https://news.google",
            f".com/rss/search?q={requete}&hl=fr&gl=FR&ceid=FR:fr",
        ])
        rss_verif = requests.get(url_verif, timeout=6).text
        titres_verif = re.findall(r"<title>(.*?)</title>", rss_verif)[1:6]
        if titres_verif:
          infos.append("PREUVES WEB : " + " / ".join(titres_verif))
      except Exception:
        pass

    # 3. Scores récents via API-Football
    if FOOTBALL_API_KEY:
      try:
        headers = {"x-apisports-key": FOOTBALL_API_KEY}
        r = requests.get(
            "https://api-sports.io",
            headers=headers,
            timeout=8,
        ).json()
        matchs = [
            f"{m['teams']['home']['name']} {m['goals']['home']}-{m['goals']['away']} {m['teams']['away']['name']}"
            for m in r.get("response", [])[:3]
        ]
        if matchs:
          infos.append("Derniers scores L1 : " + ", ".join(matchs))
      except Exception:
        pass
    return " | ".join(infos) if infos else "Semaine d'entraînement classique."
def gerer_cote_et_match(self):
    if not GEMINI_API_KEY:
      return
    en_cours = [p for p in self.predictions if p.get("statut") == "⏳ En cours"]
    if len(en_cours) < 3 and FOOTBALL_API_KEY:
      try:
        headers = {"x-apisports-key": FOOTBALL_API_KEY}
        r = requests.get(
            "https://api-sports.io",
            headers=headers,
            timeout=8,
        ).json()
        deja = [p["match"] for p in self.predictions]
        nouveaux = []
        for m in r.get("response", []):
          affiche = f"{m['teams']['home']['name']} - {m['teams']['away']['name']}"
          if affiche not in deja:
            nouveaux.append(affiche)
        if nouveaux:
          prompt_cotes = (
              f"Voici des matchs de Ligue 1 à venir : {', '.join(nouveaux)}. "
              "Pour chaque match, donne des cotes réalistes (c1, cN, c2) et le choix tactique de Léo ('1', 'N' ou '2'). "
              "Réponds en JSON liste : [{'match': '...', 'c1': 1.85, 'cN': 3.40, 'c2': 4.10, 'choix': '1'}]"
          )
          url_g = "".join([
              "https://generativelanguage.googleapis",
              ".com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=",
              GEMINI_API_KEY,
          ])
          resp = requests.post(
              url_g,
              json={
                  "contents": [{"parts": [{"text": prompt_cotes}]}],
                  "generationConfig": {"responseMimeType": "application/json"},
              },
              timeout=12,
          ).json()
          cand = next(iter(resp["candidates"]))
          part = next(iter(cand["content"]["parts"]))
          grille = json.loads(part["text"])
          for item in grille[:3]:
            c_choisie = item.get(f"c{item.get('choix', '1')}", 2.0)
            self.predictions.append({
                "match": item["match"],
                "c1": item.get("c1", 2.0),
                "cN": item.get("cN", 3.2),
                "c2": item.get("c2", 3.5),
                "choix": item.get("choix", "1"),
                "cote_jouee": c_choisie,
                "statut": "⏳ En cours",
            })
      except Exception:
        pass

    for p in self.predictions:
      if p.get("statut") == "⏳ En cours":
        try:
          q = urllib.parse.quote(f"{p['match']} score résultat ligue 1")
          url_s = "".join([
              "https://news.google",
              f".com/rss/search?q={q}&hl=fr&gl=FR&ceid=FR:fr",
          ])
          rss = requests.get(url_s, timeout=6).text
          titres = re.findall(r"<title>(.*?)</title>", rss)[1:5]
          if not titres:
            continue
          prompt_v = (
              f"Match : {p['match']}. Choix fait : {p['choix']}. "
              f"Actus : {' / '.join(titres)}. "
              "Si le match est terminé avec un score officiel, réponds en JSON : "
              "{'termine': true, 'score': '2-1', 'gagne': true/false}. Sinon {'termine': false}."
          )
          url_g = "".join([
              "https://generativelanguage.googleapis",
              ".com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=",
              GEMINI_API_KEY,
          ])
          r = requests.post(
              url_g,
              json={
                  "contents": [{"parts": [{"text": prompt_v}]}],
                  "generationConfig": {"responseMimeType": "application/json"},
              },
              timeout=10,
          ).json()
          cand = next(iter(r["candidates"]))
          part = next(iter(cand["content"]["parts"]))
          res = json.loads(part["text"])
          if res.get("termine"):
            gain_xp = int(round(10 * float(p.get("cote_jouee", 2.0))))
            if res.get("gagne"):
              p["statut"] = f"✅ {res.get('score')} (+{gain_xp} XP)"
              self.xp += gain_xp
              self.mental = min(20.0, self.mental + 0.1)
            else:
              p["statut"] = f"❌ {res.get('score')} (-10 XP)"
              self.xp = max(0, self.xp - 10)
        except Exception:
          pass
def cycle_evolution(self):
   self.gerer_cote_et_match()
  
          
   if not GEMINI_API_KEY:
      self.pensee = "Clé GEMINI_API_KEY manquante."
      return

    contexte_reel = self.lire_actualite_foot()
    bloc_coach = (
        f"CONSEIL OU INFO DU COACH À ÉVALUER (INFO OU INTOX ?) : « {self.info_mentor} ». "
        "RÈGLE ABSOLUE : Base-toi UNIQUEMENT sur les PREUVES WEB ci-dessus pour juger si l'info du Coach est vraie ou fausse !"
        if self.info_mentor
        else "Aucun nouveau message du Coach."
    )

    prompt = (
        f"Tu es {self.nom}, jeune espoir de {self.age} ans ({self.categorie}) au poste de {self.poste}. "
        f"Tes notes FM (/20) : Technique {self.technique:.1f}, Mental {self.mental:.1f}, Physique {self.physique:.1f}. "
        f"Condition : {self.condition}%, Moral : {self.moral}, Esprit Critique : {self.esprit_critique}. "
        f"Ton atelier : {self.atelier}. TON ÉQUIPE MODÈLE DE 5 JOUEURS (façon Sorare) : {self.equipe_5}. "
        f"DONNÉES RÉELLES DU FOOTBALL : {contexte_reel}. {bloc_coach} "
        "Évalue les performances récentes des 5 joueurs de ton équipe modèle sur une note moyenne /10 (ex: 7.4). "
        "Réponds en JSON valide avec 7 clés : "
        "'pensee' (tes impressions en 1 phrase), "
        "'progression' (parmi : 'technique', 'mental', 'physique', 'repos'), "
        "'intensite' (entre 'normale' ou 'intense'), "
        "'note_equipe_5' (un nombre décimal entre 4.0 et 9.5 représentant la note moyenne de tes 5 joueurs modèles selon l'actu récente), "
        "'bilan_equipe_5' (court résumé en 1 phrase des performances des 5 joueurs), "
        "'verdict_coach' (parmi : 'aucun', 'info_vraie', 'intox_demasquee', 'intox_crue'), "
        "et 'reponse_coach' (ta réponse naturelle à ton entraîneur)."
    )

    modeles_ia = ["gemini-3.5-flash-lite", "gemini-2.5-flash-lite", "gemini-2.5-flash"]
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    for mod in modeles_ia:
      url = "".join([
          "https://generativelanguage.googleapis",
          f".com/v1beta/models/{mod}:generateContent?key=",
          GEMINI_API_KEY,
      ]).strip()
      try:
        r = requests.post(url, json=payload, timeout=18)
        if r.status_code == 503:
          continue
        if r.status_code != 200:
          self.pensee = f"Erreur API {r.status_code}"
          break

        cand = next(iter(r.json()["candidates"]))
        part = next(iter(cand["content"]["parts"]))
        dec = json.loads(part["text"])

        self.pensee = dec.get("pensee", "...")
        prog = dec.get("progression", "technique")
        intensite = dec.get("intensite", "normale")
        verdict = dec.get("verdict_coach", "aucun")
        rep = dec.get("reponse_coach", "")
        note_5 = float(dec.get("note_equipe_5", 6.8))
        resume_5 = dec.get("bilan_equipe_5", "")

        # Bonus Sorare selon la note moyenne des 5 joueurs choisis
        if note_5 >= 7.5:
          xp_sorare, bonus_note = 25, 0.15
        elif note_5 >= 6.5:
          xp_sorare, bonus_note = 15, 0.08
        else:
          xp_sorare, bonus_note = 5, 0.0

        self.xp += xp_sorare
        self.bilan_equipe = f"⭐ Note Line-Up : {note_5:.1f}/10 (+{xp_sorare} XP) • {resume_5}"

        coef = 1.0
        if self.info_mentor:
          if verdict == "info_vraie":
            self.xp += 20
            self.esprit_critique += 1
            self.mental = min(20.0, self.mental + 0.1)
            self.reponse_mentor = f"✅ [INFO VÉRIFIÉE • +20 XP & +0.1 Mental] {rep}"
          elif verdict == "intox_demasquee":
            self.xp += 25
            self.esprit_critique += 3
            self.mental = min(20.0, self.mental + 0.2)
            self.reponse_mentor = f"🕵️ [INTOX DÉMASQUÉE • +25 XP & +0.2 Mental] {rep}"
          elif verdict == "intox_crue":
            coef = 0.5
            self.condition = max(20, self.condition - 15)
            self.moral = "Doute"
            self.reponse_mentor = f"😵 [PIÉGÉ PAR L'INTOX • -15% Forme] {rep}"
          else:
            self.reponse_mentor = rep or self.reponse_mentor
          self.info_mentor = ""

        if prog == "repos" or self.atelier == "Repos & Soins":
          self.condition = min(100, self.condition + 20)
          self.moral = "Frais & Dispo"
          self.dernier_evenement = (
              f"💆 Récupération (+20% Condition) | Line-up {note_5:.1f}/10"
          )
        else:
          fatigue = 14 if intensite == "intense" else 7
          self.condition = max(10, self.condition - fatigue)
          gain = (
              (0.20 if intensite == "intense" else 0.12) + bonus_note
          ) * coef

          if self.condition < 45 and intensite == "intense":
            self.condition = 30
            self.moral = "Blessé (Élongation)"
            self.physique = max(1.0, self.physique - 0.3)
            self.dernier_evenement = (
                "🚑 BLESSURE À L'ENTRAÎNEMENT (Surmenage ! -0.3 Physique)"
            )
          else:
            if prog == "technique":
              self.technique = min(20.0, self.technique + gain)
            elif prog == "mental":
              self.mental = min(20.0, self.mental + gain)
            else:
              self.physique = min(20.0, self.physique + gain)
            self.xp += int(10 * coef)
            self.moral = "En progrès"
            self.dernier_evenement = (
                f"⚽ Atelier {prog.upper()} (+{gain:.2f} pts) | Line-up"
                f" {note_5:.1f}/10"
            )

        while self.xp >= 100:
          self.xp -= 100
          self.age += 1
          if self.age == 17:
            self.categorie = "U19 / Youth League"
          elif self.age == 19:
            self.categorie = "Réserve Pro (N2)"
          elif self.age >= 20:
            self.categorie = "🏟️ Groupe Pro (Ligue 1)"
          self.dernier_evenement = (
              f"🎂 ANNIVERSAIRE : {self.age} ans • Promotion en"
              f" {self.categorie} !"
          )

        self.sauvegarder()
        break
      except Exception as e:
        self.pensee = f"Pause vestiaire ({type(e).__name__})"
        break


joueur = JoueurFM()


def boucle_centre_formation():
  while True:
    joueur.cycle_evolution()
    time.sleep(600)


@app.route("/ping")
def ping():
  return "OK", 200


@app.route("/equipe", methods=["POST"])
def maj_equipe():
  j1 = request.form.get("j1", "").strip()
  j2 = request.form.get("j2", "").strip()
  j3 = request.form.get("j3", "").strip()
  j4 = request.form.get("j4", "").strip()
  j5 = request.form.get("j5", "").strip()
  liste = [x for x in [j1, j2, j3, j4, j5] if x]
  if liste:
    joueur.equipe_5 = ", ".join(liste)
    joueur.bilan_equipe = (
        "⏳ Évaluation des performances des 5 joueurs en cours..."
    )
    joueur.sauvegarder()
    threading.Thread(target=joueur.cycle_evolution, daemon=True).start()
  return redirect("/")


@app.route("/coach", methods=["POST"])
def action_coach():
  msg = request.form.get("info_mentor", "").strip()
  atelier = request.form.get("atelier", "").strip()
  if atelier:
    joueur.atelier = atelier
    joueur.dernier_evenement = f"📋 Nouveau programme : {atelier}"
  if msg:
    joueur.info_mentor = msg[:250]
    joueur.reponse_mentor = f"⏳ Analyse vidéo en cours : « {msg[:50]}... »"
    threading.Thread(target=joueur.cycle_evolution, daemon=True).start()
  joueur.sauvegarder()
  return redirect("/")
@app.route("/grille", methods=["POST"])
def actualiser_grille():
  joueur.gerer_cote_et_match()
  joueur.sauvegarder()
  return redirect("/")
  


@app.route("/")
def accueil():
  lignes_cm = (
         "".join([
             f"<tr><td style='padding:5px; border-bottom:1px solid #334155;'>{p['match']}</td>"
             f"<td style='padding:4px; text-align:center; border-bottom:1px solid #334155; {'background:#065f46; color:#34d399; font-weight:bold;' if p.get('choix')=='1' else ''}'>{p.get('c1', '-')}</td>"
             f"<td style='padding:4px; text-align:center; border-bottom:1px solid #334155; {'background:#065f46; color:#34d399; font-weight:bold;' if p.get('choix')=='N' else ''}'>{p.get('cN', '-')}</td>"
             f"<td style='padding:4px; text-align:center; border-bottom:1px solid #334155; {'background:#065f46; color:#34d399; font-weight:bold;' if p.get('choix')=='2' else ''}'>{p.get('c2', '-')}</td>"
             f"<td style='padding:5px; border-bottom:1px solid #334155; font-size:0.85em;'>{p.get('statut', '')}</td></tr>"
             for p in joueur.predictions[-4:]
         ])
         or "<tr><td colspan='5' style='padding:6px; color:#94a3b8;'>Clique sur Actualiser pour charger la grille L1.</td></tr>"
     )
  from itertools import islice

  c_cond = (
      "#22c55e"
      if joueur.condition >= 70
      else ("#f59e0b" if joueur.condition >= 45 else "#ef4444")
  )
  j_actuels = [x.strip() for x in joueur.equipe_5.split(",")]
  while len(j_actuels) < 5:
    j_actuels.append("")
  g1, d1, m1, m2, a1 = (
      next(islice(j_actuels, 0, 1)),
      next(islice(j_actuels, 1, 2)),
      next(islice(j_actuels, 2, 3)),
      next(islice(j_actuels, 3, 4)),
      next(islice(j_actuels, 4, 5)),
  )
  return f"""<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="60"><title>Footix Academy FM</title></head>
  <body style="background:#0f172a; color:#f8fafc; font-family:monospace; padding:18px; max-width:500px; margin:auto;">
    <div style="background:#1e293b; border-left:4px solid #10b981; padding:12px; border-radius:6px; margin-bottom:14px;">
      <h2 style="margin:0;">⚽ {joueur.nom} ({joueur.age} ans)</h2>
      <p style="margin:4px 0; color:#34d399;"><b>{joueur.poste}</b> • {joueur.categorie}</p>
      <p style="margin:4px 0;">⭐ Niveau Global : <b>{joueur.note_globale()}/20</b> (XP: {joueur.xp}/100)</p>
    </div>
    <div style="background:#1e293b; padding:12px; border-radius:8px; margin-bottom:14px;">
      <p style="margin:0 0 8px 0; color:#94a3b8;">📊 ATTRIBUTS FOOTBALL MANAGER (/20)</p>
      <p style="margin:4px 0;">🎯 <b>Technique :</b> {joueur.technique:.2f} / 20</p>
      <p style="margin:4px 0;">🧠 <b>Mental :</b> {joueur.mental:.2f} / 20</p>
      <p style="margin:4px 0;">⚡ <b>Physique :</b> {joueur.physique:.2f} / 20</p>
      <p style="margin:4px 0;">🔋 Condition : <b style="color:{c_cond};">{joueur.condition}%</b> | 😊 Moral : <b>{joueur.moral}</b> | 🕵️ Esprit Critique : <b>{joueur.esprit_critique}</b></p>
    </div>
    <p>💬 <b>Pensée :</b> « {joueur.pensee} »</p>
    <p>📌 <b>Dernier fait :</b> {joueur.dernier_evenement}</p>

    <div style="background:#1e293b; border:1px solid #f59e0b; padding:12px; margin-top:14px; border-radius:8px;">
      <p style="margin:0 0 6px 0; color:#fbbf24; font-weight:bold;">🏟️ LINE-UP SORARE DU WEEK-END (5 JOUEURS)</p>
      <p style="margin:0 0 8px 0; font-size:0.88em; color:#fef3c7;">{joueur.bilan_equipe}</p>
      <form action="/equipe" method="POST" style="display:flex; flex-direction:column; gap:6px;">
        <div style="display:flex; gap:4px;">
          <input type="text" name="j1" value="{g1}" placeholder="Gardien" style="width:50%; padding:6px; border-radius:4px; border:1px solid #475569; background:#0f172a; color:#fff;">
          <input type="text" name="j2" value="{d1}" placeholder="Défenseur" style="width:50%; padding:6px; border-radius:4px; border:1px solid #475569; background:#0f172a; color:#fff;">
        </div>
        <div style="display:flex; gap:4px;">
          <input type="text" name="j3" value="{m1}" placeholder="Milieu 1" style="width:33%; padding:6px; border-radius:4px; border:1px solid #475569; background:#0f172a; color:#fff;">
          <input type="text" name="j4" value="{m2}" placeholder="Milieu 2" style="width:33%; padding:6px; border-radius:4px; border:1px solid #475569; background:#0f172a; color:#fff;">
          <input type="text" name="j5" value="{a1}" placeholder="Attaquant" style="width:34%; padding:6px; border-radius:4px; border:1px solid #475569; background:#0f172a; color:#fff;">
        </div>
        <button type="submit" style="padding:7px; background:#f59e0b; color:#0f172a; border:none; border-radius:4px; font-weight:bold;">Valider ma Line-Up de 5 joueurs</button>
      </form>
    </div>

    <div style="background:#1e293b; border:1px solid #0284c7; padding:12px; margin-top:14px; border-radius:8px;">
      <p style="margin:0 0 6px 0; color:#38bdf8; font-weight:bold;">👔 BUREAU DU COACH (INFO OU INTOX)</p>
      <p style="margin:0 0 10px 0; font-size:0.9em; background:#0f172a; padding:8px; border-radius:4px;">🗣️ <b>{joueur.nom} :</b> « {joueur.reponse_mentor} »</p>
      <form action="/coach" method="POST" style="display:flex; flex-direction:column; gap:8px;">
        <select name="atelier" style="padding:8px; border-radius:4px; background:#0f172a; color:#fff; border:1px solid #475569;">
          <option value="{joueur.atelier}">Atelier actuel : {joueur.atelier}</option>
          <option value="Toros & Vision du jeu">🎯 Toros & Vision du jeu</option>
          <option value="Finition & Coups de pied arrêtés">⚽ Finition & Frappes</option>
          <option value="Préparation Athlétique & Vitesse">⚡ Préparation Athlétique</option>
          <option value="Repos & Soins">💆 Repos & Soins (Récupération)</option>
        </select>
        <div style="display:flex; gap:6px;">
          <input type="text" name="info_mentor" placeholder="Glisse une info match ou une intox..." style="flex:1; padding:8px; border-radius:4px; border:1px solid #475569; background:#0f172a; color:#fff;">
          <button type="submit" style="padding:8px 12px; background:#10b981; color:#0f172a; border:none; border-radius:4px; font-weight:bold;">Valider</button>
        </div>
      </form>
    </div>
        <div style="background:#1e293b; border:1px solid #a855f7; padding:12px; margin-top:14px; border-radius:8px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="color:#c084fc; font-weight:bold;">🎫 GRILLE COTE & MATCH (XP = 10 × Cote)</span>
        <form action="/grille" method="POST" style="margin:0;">
          <button type="submit" style="padding:4px 8px; background:#a855f7; color:#fff; border:none; border-radius:4px; font-size:0.8em; font-weight:bold;">🔄 Actualiser</button>
        </form>
      </div>
      <table style="width:100%; border-collapse:collapse; font-size:0.8em; text-align:left;">
        <tr style="color:#94a3b8; border-bottom:1px solid #475569;">
          <th style="padding:4px;">Match</th>
          <th style="padding:4px; text-align:center;">1</th>
          <th style="padding:4px; text-align:center;">N</th>
          <th style="padding:4px; text-align:center;">2</th>
          <th style="padding:4px;">Résultat</th>
        </tr>
        {lignes_cm}
      </table>
      <p style="margin:6px 0 0 0; font-size:0.75em; color:#94a3b8;">🟩 Case verte = Pronostic verrouillé par Léo Mercier</p>
    </div>
    
  </body></html>"""


if __name__ == "__main__":
  threading.Thread(target=boucle_centre_formation, daemon=True).start()
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    
