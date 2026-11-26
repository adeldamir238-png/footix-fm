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
    self.modeles = ["Vitinha", "Warren Zaïre-Emery", "Pedri"]
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
      }
      requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception:
      pass

  def lire_actualite_foot(self):
    infos = []
    try:
      url_rss = "".join([
          "https://news.google",
          ".com/rss/search?q=ligue+1+champions+league+football&hl=fr&gl=FR&ceid=FR:fr",
      ])
      rss = requests.get(url_rss, timeout=6).text
      titres = re.findall(r"<title>(.*?)</title>", rss)[1:5]
      if titres:
        infos.append("Actus Foot : " + " / ".join(titres))
    except Exception:
      pass
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
          infos.append(
              "PREUVES WEB EN DIRECT SUR L'INFO DU COACH : "
              + " / ".join(titres_verif)
          )
      except Exception:
        pass
        
              + " / ".join(titres_verif)
          )
      except Exception:
        pass
        
    
        
    if FOOTBALL_API_KEY:
      try:
        headers = {"x-apisports-key": FOOTBALL_API_KEY}
        r = requests.get(
            "https://api-sports.io",
            headers=headers,
            timeout=8,
        ).json()
        matchs = []
        for m in r.get("response", [])[:3]:
          eq1 = m["teams"]["home"]["name"]
          eq2 = m["teams"]["away"]["name"]
          g1 = m["goals"]["home"]
          g2 = m["goals"]["away"]
          matchs.append(f"{eq1} {g1}-{g2} {eq2}")
        if matchs:
          infos.append("Derniers scores L1 : " + ", ".join(matchs))
      except Exception:
        pass
    return " | ".join(infos) if infos else "Semaine d'entraînement classique."

  def cycle_evolution(self):
    if not GEMINI_API_KEY:
      self.pensee = "Clé GEMINI_API_KEY manquante."
      return

    contexte_reel = self.lire_actualite_foot()
    bloc_coach = (
        f"CONSEIL OU INFO DU COACH À ÉVALUER (INFO OU INTOX ?) : « {self.info_mentor} ». "
        "RÈGLE ABSOLUE : Ne te fie JAMAIS à tes vieux souvenirs pour les transferts ou résultats ! "
        "Base-toi UNIQUEMENT sur les PREUVES WEB EN DIRECT ci-dessus : si les titres d'actualité confirment les mots du Coach (même un transfert récent), mets 'info_vraie' !"
        if self.info_mentor
        else "Aucun nouveau message du Coach."
        )
    

    prompt = (
        f"Tu es {self.nom}, jeune espoir de {self.age} ans ({self.categorie}) au poste de {self.poste}. "
        f"Tes notes FM (/20) : Technique {self.technique:.1f}, Mental {self.mental:.1f}, Physique {self.physique:.1f}. "
        f"Condition : {self.condition}%, Moral : {self.moral}, Esprit Critique : {self.esprit_critique}. "
        f"Ton atelier de la semaine : {self.atelier}. Tes modèles pros : {', '.join(self.modeles)}. "
        f"DONNÉES RÉELLES DU FOOTBALL : {contexte_reel}. {bloc_coach} "
        "Réponds en JSON valide avec 5 clés : "
        "'pensee' (tes impressions d'entraînement ou d'observation des pros en 1 phrase), "
        "'progression' (choisis parmi : 'technique', 'mental', 'physique', 'repos'), "
        "'intensite' (choisis entre 'normale' ou 'intense' - attention au risque de blessure si condition < 65% !), "
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
        r = requests.post(url, json=payload, timeout=15)
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

        coef = 1.0
        if self.info_mentor:
          if verdict == "info_vraie":
            self.xp += 20
            self.esprit_critique += 1
            self.reponse_mentor = f"✅ [INFO VÉRIFIÉE • +20 XP] {rep}"
          elif verdict == "intox_demasquee":
            self.xp += 25
            self.esprit_critique += 3
            self.mental = min(20.0, self.mental + 0.2)
            self.reponse_mentor = f"🕵️ [INTOX DÉMASQUÉE • +0.2 Mental] {rep}"
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
          self.dernier_evenement = "💆 Séance de récupération (+20% Condition)"
        else:
          fatigue = 14 if intensite == "intense" else 7
          self.condition = max(10, self.condition - fatigue)
          gain = (0.25 if intensite == "intense" else 0.15) * coef

          if self.condition < 45 and intensite == "intense":
            self.condition = 30
            self.moral = "Blessé (Élongation)"
            self.physique = max(1.0, self.physique - 0.3)
            self.dernier_evenement = "🚑 BLESSURE À L'ENTRAÎNEMENT (Surmenage ! -0.3 Physique)"
          else:
            if prog == "technique":
              self.technique = min(20.0, self.technique + gain)
            elif prog == "mental":
              self.mental = min(20.0, self.mental + gain)
            else:
              self.physique = min(20.0, self.physique + gain)
            self.xp += int(15 * coef)
            self.moral = "En progrès"
            self.dernier_evenement = f"⚽ Atelier {prog.upper()} (+{gain:.2f} pts)"

        while self.xp >= 100:
          self.xp -= 100
          self.age += 1
          if self.age == 17:
            self.categorie = "U19 / Youth League"
          elif self.age == 19:
            self.categorie = "Réserve Pro (N2)"
          elif self.age >= 20:
            self.categorie = "🏟️ Groupe Pro (Ligue 1)"
          self.dernier_evenement = f"🎂 ANNIVERSAIRE : {self.age} ans • Promotion en {self.categorie} !"

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


@app.route("/")
def accueil():
  c_cond = (
      "#22c55e"
      if joueur.condition >= 70
      else ("#f59e0b" if joueur.condition >= 45 else "#ef4444")
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
      <p style="margin:4px 0;">🔋 Condition : <b style="color:{c_cond};">{joueur.condition}%</b> | 😊 Moral : <b>{joueur.moral}</b></p>
      <p style="margin:4px 0;">🕵️ Esprit Critique : <b>{joueur.esprit_critique}</b> | Modèles : {', '.join(joueur.modeles)}</p>
    </div>
    <p>💬 <b>Pensée du joueur :</b> « {joueur.pensee} »</p>
    <p>📌 <b>Dernier fait :</b> {joueur.dernier_evenement}</p>
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
  </body></html>"""


if __name__ == "__main__":
  threading.Thread(target=boucle_centre_formation, daemon=True).start()
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
  



