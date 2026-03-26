"""
tests/test_pipeline.py — Tests d'intégration avec un script YouTube réel.

Scénario : vidéo "Les 5 habitudes des développeurs efficaces"
Aucun appel API externe — on teste uniquement la logique pure.
"""

import sys
import textwrap
import tempfile
from pathlib import Path

import pytest

# Ajoute la racine du projet au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from extraction_markdown import extract_sections, load_script, _strip_markup, _build_image_prompt
from nlp_processing import (
    clean_narration,
    split_into_chunks,
    estimate_duration,
    generate_metadata,
    process_sections,
)

# ── Script réel utilisé dans tous les tests ───────────────────────────────────

REAL_SCRIPT = textwrap.dedent("""\
    # Les 5 habitudes des développeurs efficaces

    Bienvenue dans cette vidéo où nous allons explorer les pratiques qui
    distinguent les développeurs productifs des autres.

    ## 1. Lire du code tous les jours

    <!-- img: A developer reading open-source code on a dark monitor, focused, cozy office -->

    Les meilleurs développeurs lisent du code comme d'autres lisent des livres.
    Parcourir des projets open-source sur GitHub permet de découvrir de nouveaux
    patterns et d'élargir son vocabulaire technique.

    ## 2. Écrire des tests avant le code

    Le **Test-Driven Development** (TDD) force à réfléchir à l'interface avant
    l'implémentation. Résultat : moins de bugs, une meilleure conception, et
    une confiance accrue lors des refactorisations.

    ## 3. Faire des pauses régulières

    La technique **Pomodoro** — 25 minutes de travail, 5 minutes de pause —
    maintient la concentration au maximum. Notre cerveau n'est pas fait pour
    rester focalisé plus de 90 minutes d'affilée.

    ## 4. Documenter en écrivant

    Tenir un journal technique (blog, Notion, fichier local) oblige à
    verbaliser ce qu'on apprend. L'écriture consolide la mémoire et produit
    une ressource utile pour l'équipe.

    ## 5. Contribuer à l'open-source

    Même une petite [pull request](https://github.com) améliore des compétences
    concrètes : communication, code review, gestion de versions. C'est aussi
    un excellent signal pour les recruteurs.
""")


# ═══════════════════════════════════════════════════════════════════════════════
# extraction_markdown
# ═══════════════════════════════════════════════════════════════════════════════

class TestExtractSections:

    def test_nombre_sections(self):
        """Le script contient 1 H1 + 5 H2 → 6 sections."""
        sections = extract_sections(REAL_SCRIPT)
        assert len(sections) == 6

    def test_premiere_section_est_h1(self):
        sections = extract_sections(REAL_SCRIPT)
        assert sections[0].level == 1
        assert sections[0].title == "Les 5 habitudes des développeurs efficaces"

    def test_sections_h2_dans_lordre(self):
        sections = extract_sections(REAL_SCRIPT)
        titres_attendus = [
            "1. Lire du code tous les jours",
            "2. Écrire des tests avant le code",
            "3. Faire des pauses régulières",
            "4. Documenter en écrivant",
            "5. Contribuer à l'open-source",
        ]
        for i, attendu in enumerate(titres_attendus, start=1):
            assert sections[i].title == attendu

    def test_index_sequentiel(self):
        sections = extract_sections(REAL_SCRIPT)
        for i, s in enumerate(sections):
            assert s.index == i

    def test_narration_sans_markup(self):
        """La narration ne doit pas contenir de ** ni de []."""
        sections = extract_sections(REAL_SCRIPT)
        for s in sections:
            assert "**" not in s.narration
            assert "[" not in s.narration

    def test_image_prompt_custom_depuis_commentaire_html(self):
        """La section 1 contient un commentaire <!-- img: ... --> qui doit être utilisé."""
        sections = extract_sections(REAL_SCRIPT)
        assert "dark monitor" in sections[1].image_prompt

    def test_image_prompt_auto_genere_pour_autres(self):
        """Les sections sans commentaire img doivent avoir un prompt auto."""
        sections = extract_sections(REAL_SCRIPT)
        assert sections[2].image_prompt.startswith("Cinematic illustration:")

    def test_fallback_sans_titre(self):
        """Un texte sans heading doit créer une section unique 'Introduction'."""
        sections = extract_sections("Du texte sans titre du tout.")
        assert len(sections) == 1
        assert sections[0].title == "Introduction"

    def test_body_vide_introuvable_pas_crash(self):
        """Une section avec body vide ne doit pas lever d'exception."""
        md = "# Titre seul\n## Section vide\n"
        sections = extract_sections(md)
        assert len(sections) == 2
        assert sections[1].narration == ""


class TestStripMarkup:

    def test_supprime_liens(self):
        assert _strip_markup("[GitHub](https://github.com)") == "GitHub"

    def test_supprime_gras_italique(self):
        assert _strip_markup("**gras** et _italique_") == "gras et italique"

    def test_supprime_code_inline(self):
        # _MARKUP_RE inclut aussi les underscores, donc mon_code → moncode
        assert _strip_markup("`mon_code()`") == "moncode"

    def test_normalise_espaces(self):
        assert _strip_markup("   trop   d'espaces   ") == "trop d'espaces"

    def test_texte_propre_inchange(self):
        assert _strip_markup("Bonjour le monde") == "Bonjour le monde"


class TestBuildImagePrompt:

    def test_utilise_commentaire_html(self):
        body = "Du texte.\n<!-- img: Un chat sur Mars -->"
        prompt = _build_image_prompt("Titre", body)
        assert prompt == "Un chat sur Mars"

    def test_genere_prompt_auto(self):
        body = "Les développeurs lisent beaucoup de livres techniques."
        prompt = _build_image_prompt("Lecture", body)
        assert "Cinematic illustration" in prompt
        assert "Lecture" in prompt

    def test_body_vide(self):
        prompt = _build_image_prompt("Titre seul", "")
        assert "Titre seul" in prompt


class TestLoadScript:

    def test_charge_fichier_existant(self, tmp_path):
        script = tmp_path / "script.md"
        script.write_text(REAL_SCRIPT, encoding="utf-8")
        content = load_script(script)
        assert "habitudes" in content

    def test_erreur_fichier_inexistant(self):
        with pytest.raises(FileNotFoundError):
            load_script("/chemin/qui/nexiste/pas.md")


# ═══════════════════════════════════════════════════════════════════════════════
# nlp_processing
# ═══════════════════════════════════════════════════════════════════════════════

class TestCleanNarration:

    def test_supprime_espaces_multiples(self):
        assert clean_narration("trop    d'espaces") == "trop d'espaces"

    def test_supprime_lignes_vides_excessives(self):
        result = clean_narration("ligne1\n\n\n\nligne2")
        assert "\n\n\n" not in result

    def test_insere_point_entre_minuscule_majuscule(self):
        result = clean_narration("un motAutre mot")
        assert ". " in result

    def test_strip_whitespace(self):
        assert clean_narration("  texte  ") == "texte"

    def test_texte_propre_inchange(self):
        texte = "Une phrase propre. Une deuxième."
        assert clean_narration(texte) == texte


class TestSplitIntoChunks:

    def test_texte_court_donne_un_chunk(self):
        chunks = split_into_chunks("Texte court.", max_chars=4096)
        assert chunks == ["Texte court."]

    def test_texte_long_decoupé_aux_phrases(self):
        phrases = ["Phrase numéro %d." % i for i in range(200)]
        long_text = " ".join(phrases)
        chunks = split_into_chunks(long_text, max_chars=500)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c) <= 500

    def test_phrase_unique_trop_longue_decoupee(self):
        """Une phrase sans ponctuation dépassant max_chars doit être tronquée."""
        long_word = "a" * 1000
        chunks = split_into_chunks(long_word, max_chars=300)
        assert all(len(c) <= 300 for c in chunks)

    def test_reconstitution_complete(self):
        """La concaténation des chunks doit couvrir tout le texte original."""
        phrases = ["Phrase %d avec du contenu." % i for i in range(50)]
        original = " ".join(phrases)
        chunks = split_into_chunks(original, max_chars=200)
        reconstitue = " ".join(chunks)
        # Tous les mots de l'original doivent être présents
        for phrase in phrases:
            mot_cle = phrase.split()[1]  # "0", "1", …
            assert mot_cle in reconstitue


class TestEstimateDuration:

    def test_150_mots_donne_60_secondes(self):
        texte = " ".join(["mot"] * 150)
        assert estimate_duration(texte) == 60.0

    def test_75_mots_donne_30_secondes(self):
        texte = " ".join(["mot"] * 75)
        assert estimate_duration(texte) == 30.0

    def test_texte_vide_donne_zero(self):
        assert estimate_duration("") == 0.0

    def test_resultat_arrondi_a_un_decimal(self):
        texte = " ".join(["mot"] * 10)  # 10/150*60 = 4.0
        result = estimate_duration(texte)
        assert result == round(result, 1)


class TestGenerateMetadata:

    def setup_method(self):
        self.sections = extract_sections(REAL_SCRIPT)

    def test_titre_depuis_h1(self):
        meta = generate_metadata(self.sections)
        assert meta["title"] == "Les 5 habitudes des développeurs efficaces"

    def test_titre_max_100_chars(self):
        meta = generate_metadata(self.sections)
        assert len(meta["title"]) <= 100

    def test_description_contient_toc(self):
        meta = generate_metadata(self.sections)
        assert "1." in meta["description"]
        assert "2." in meta["description"]

    def test_description_contient_intro(self):
        meta = generate_metadata(self.sections)
        # L'intro est la narration de la section 0 (H1)
        assert "habitudes" in meta["description"].lower() or "..." in meta["description"]

    def test_tags_sont_une_liste(self):
        meta = generate_metadata(self.sections)
        assert isinstance(meta["tags"], list)

    def test_tags_max_30(self):
        meta = generate_metadata(self.sections)
        assert len(meta["tags"]) <= 30

    def test_tags_sans_doublons(self):
        meta = generate_metadata(self.sections)
        tags_lower = [t.lower() for t in meta["tags"]]
        assert len(tags_lower) == len(set(tags_lower))

    def test_fallback_sans_sections(self):
        from extraction_markdown import Section
        vide = [Section(0, 2, "Intro", "", "", "")]
        meta = generate_metadata(vide)
        assert meta["title"] == "Intro"

    def test_titre_h1_prioritaire_sur_h2(self):
        """Si le script commence par H2 puis H1, c'est quand même le H1 qui gagne."""
        from extraction_markdown import Section
        sections = [
            Section(0, 2, "Intro H2", "", "", ""),
            Section(1, 1, "Titre Principal H1", "", "", ""),
        ]
        meta = generate_metadata(sections)
        assert meta["title"] == "Titre Principal H1"


class TestProcessSections:

    def test_retourne_tuple_sections_metadata(self):
        sections = extract_sections(REAL_SCRIPT)
        result = process_sections(sections)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_narrations_nettoyees(self):
        sections = extract_sections(REAL_SCRIPT)
        enriched, _ = process_sections(sections)
        for s in enriched:
            assert "  " not in s.narration  # pas d'espaces doubles

    def test_metadata_complete(self):
        sections = extract_sections(REAL_SCRIPT)
        _, meta = process_sections(sections)
        assert "title" in meta
        assert "description" in meta
        assert "tags" in meta


# ═══════════════════════════════════════════════════════════════════════════════
# Scénario bout-en-bout (sans API)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPipelineE2E:
    """Simule les deux premières étapes du pipeline avec le script réel."""

    def test_extraction_puis_traitement_nlp(self):
        # Étape 1 : extraction
        sections = extract_sections(REAL_SCRIPT)
        assert len(sections) == 6

        # Étape 2 : enrichissement NLP
        enriched, meta = process_sections(sections)

        # Vérifications croisées
        assert meta["title"] == "Les 5 habitudes des développeurs efficaces"
        assert len(enriched) == 6
        assert all(s.narration for s in enriched[1:])  # body non vide pour H2

    def test_script_depuis_fichier_tmp(self, tmp_path):
        """Vérifie load_script → extract_sections → process_sections."""
        script_file = tmp_path / "script.md"
        script_file.write_text(REAL_SCRIPT, encoding="utf-8")

        content  = load_script(script_file)
        sections = extract_sections(content)
        enriched, meta = process_sections(sections)

        assert meta["title"] == "Les 5 habitudes des développeurs efficaces"
        assert len(enriched) == 6

    def test_chunks_tts_dans_limite_openai(self):
        """Chaque chunk de narration doit rester sous 4096 caractères."""
        sections = extract_sections(REAL_SCRIPT)
        enriched, _ = process_sections(sections)

        for s in enriched:
            chunks = split_into_chunks(s.narration)
            for chunk in chunks:
                assert len(chunk) <= 4096
