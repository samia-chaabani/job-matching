"""
Interface Streamlit - Job Matching
"""
import os
import sys
import tempfile
import streamlit as st
import pandas as pd

# Ajouter le dossier racine au path pour importer matching
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from matching.matcher import extract_text, extract_skills, match_cv

# ============================================================
# CONFIG PAGE
# ============================================================
st.set_page_config(
    page_title="Job Matching - CV Analyzer",
    page_icon="🎯",
    layout="wide",
)

# ============================================================
# STYLE CSS
# ============================================================
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .score-badge {
        background-color: #1f77b4;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
    }
    .skills-common {
        color: #28a745;
        font-weight: bold;
    }
    .skills-missing {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown('<div class="main-title">🎯 Job Matching</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Uploadez votre CV et trouvez les offres qui vous correspondent</div>', unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("⚙️ Paramètres")
    top_k = st.slider("Nombre d'offres à afficher", min_value=5, max_value=50, value=10, step=5)
    min_score = st.slider("Score minimum (%)", min_value=0, max_value=100, value=0, step=5)

    st.markdown("---")
    st.markdown("### 📖 Comment ça marche ?")
    st.markdown("""
    1. **Uploadez** votre CV (PDF ou DOCX)
    2. Le système **extrait** vos compétences
    3. Il **compare** avec 3376 offres d'emploi
    4. Il renvoie les **meilleures correspondances** avec un score
    """)

# ============================================================
# UPLOAD
# ============================================================
col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader(
        "📄 Uploadez votre CV (PDF ou DOCX)",
        type=["pdf", "docx"],
        help="Formats acceptés : PDF, DOCX"
    )

with col2:
    st.markdown("### 💡 Astuce")
    st.info("Le CV doit être en **PDF** ou **DOCX**. Évitez les images scannées.")

# ============================================================
# TRAITEMENT
# ============================================================
if uploaded_file is not None:
    # Sauvegarde temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        with st.spinner("📄 Extraction du texte du CV..."):
            cv_text = extract_text(tmp_path)

        if not cv_text.strip():
            st.error("❌ Impossible d'extraire le texte. Le PDF est peut-être scanné (image).")
            st.stop()

        with st.spinner("🔍 Analyse et matching en cours..."):
            results, cv_skills = match_cv(cv_text, top_k=top_k)

        # Filtre score minimum
        results = [r for r in results if r["score"] >= min_score]

        # ============================================================
        # AFFICHAGE DES COMPÉTENCES DU CV
        # ============================================================
        st.markdown("---")
        st.subheader("🧠 Compétences détectées dans votre CV")

        if cv_skills:
            cols = st.columns(min(len(cv_skills), 8))
            for i, skill in enumerate(cv_skills):
                cols[i % 8].markdown(
                    f'<span style="background:#e3f2fd; color:#1f77b4; padding:4px 10px; '
                    f'border-radius:12px; margin:2px; display:inline-block;">{skill}</span>',
                    unsafe_allow_html=True
                )
        else:
            st.warning("⚠️ Aucune compétence technique détectée. Vérifiez votre CV.")

        # ============================================================
        # AFFICHAGE DES RÉSULTATS
        # ============================================================
        st.markdown("---")
        st.subheader(f"🎯 Top {len(results)} offres qui vous correspondent")

        if not results:
            st.warning("Aucune offre ne correspond à vos critères. Essayez de baisser le score minimum.")
        else:
            for i, r in enumerate(results, 1):
                with st.container():
                    col_left, col_right = st.columns([3, 1])

                    with col_left:
                        st.markdown(f"### {i}. {r['titre']}")
                        st.markdown(f"🏢 **{r['entreprise']}** &nbsp;&nbsp;|&nbsp;&nbsp; 📍 {r['lieu']}")

                        # Compétences communes
                        if r["competences_communes"]:
                            st.markdown(
                                "✅ **Compétences communes** : " +
                                ", ".join(f"`{s}`" for s in r["competences_communes"])
                            )

                        # Compétences manquantes
                        if r["competences_manquantes"]:
                            st.markdown(
                                "⚠️ **À apprendre** : " +
                                ", ".join(f"`{s}`" for s in r["competences_manquantes"])
                            )

                        # Lien
                        if r["url"]:
                            st.markdown(f"[🔗 Voir l'offre complète]({r['url']})")

                    with col_right:
                        st.metric("Score", f"{r['score']}%", f"Similarité {r['similarite']}%")

                    st.markdown("---")

        # ============================================================
        # EXPORT CSV
        # ============================================================
        st.subheader("📥 Exporter les résultats")
        df = pd.DataFrame(results)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Télécharger en CSV",
            data=csv,
            file_name="matching_results.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"❌ Erreur lors du traitement : {e}")
    finally:
        os.unlink(tmp_path)

else:
    # Écran d'accueil
    st.markdown("---")
    st.info("👆 **Commencez par uploader votre CV** pour voir les offres qui vous correspondent.")