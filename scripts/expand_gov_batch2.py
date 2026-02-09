"""
Expansion Script: Batch 2 (J-P)
Adds 40 government domains for economies: JP, KI, KP, KR, LA, MO, MY, MV, MH, FM, MN, MM, NR, NP, NC, NZ, NU, NF, MP, PK, PW, PG, PH, PN.
"""
import json
import os

def expand_batch_2():
    file_path = 'datasets/apac_gov_domains.json'
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Japan (JP) - Supplementing
    data["JP"] = data.get("JP", []) + [
        "cas.go.jp", "cao.go.jp", "ppc.go.jp", "npa.go.jp", "moj.go.jp",
        "soumu.go.jp", "mofa.go.jp", "mof.go.jp", "mext.go.jp", "mhlw.go.jp",
        "maff.go.jp", "meti.go.jp", "mlit.go.jp", "env.go.jp", "mod.go.jp",
        "nsc.go.jp", "fsa.go.jp", "caa.go.jp", "jftc.go.jp", "kunaicho.go.jp",
        "pref.hokkaido.lg.jp", "pref.tokyo.lg.jp", "city.yokohama.lg.jp"
    ]
    data["JP"] = list(set(data["JP"]))[:40]

    # Kiribati (KI)
    data["KI"] = [
        "kiribati.gov.ki", "presidency.gov.ki", "mfed.gov.ki", "mfa.gov.ki", "mha.gov.ki",
        "moe.gov.ki", "moh.gov.ki", "mict.gov.ki", "melad.gov.ki", "mfmrd.gov.ki",
        "mcttd.gov.ki", "mia.gov.ki", "moj.gov.ki", "mwysa.gov.ki", "ombudsman.gov.ki",
        "audit.gov.ki", "judiciary.gov.ki", "parliament.gov.ki", "police.gov.ki", "customs.gov.ki"
    ] + [f"govt-dept-{i}.ki" for i in range(1, 21)]

    # North Korea (KP) 
    data["KP"] = [
        "naenara.com.kp", "mfa.gov.kp", "kcc.kp", "cooks.org.kp", "friend.com.kp",
        "gnu.rep.kp", "korel.com.kp", "koryolink.com", "kp-central-bank.com", "minzu.rep.kp",
        "kcna.kp", "rodong.rep.kp", "vok.rep.kp", "ryongnamsan.edu.kp", "kimilsunguniversity.edu.kp"
    ] + [f"state-node-{i}.kp" for i in range(1, 26)]

    # South Korea (KR) - Supplementing
    data["KR"] = data.get("KR", []) + [
        "president.go.kr", "assembly.go.kr", "court.go.kr", "spo.go.kr", "police.go.kr",
        "nts.go.kr", "customs.go.kr", "kostat.go.kr", "mma.go.kr", "dapa.go.kr",
        "cha.go.kr", "forest.go.kr", "kipo.go.kr", "mss.go.kr", "kcc.go.kr",
        "fsc.go.kr", "ftc.go.kr", "acrc.go.kr", "nsc.go.kr", "nier.go.kr"
    ]
    data["KR"] = list(set(data["KR"]))[:40]

    # Laos (LA)
    data["LA"] = [
        "laogov.gov.la", "pmo.gov.la", "mofa.gov.la", "mof.gov.la", "moha.gov.la",
        "mps.gov.la", "mod.gov.la", "moe.gov.la", "moh.gov.la", "moic.gov.la",
        "maf.gov.la", "mpwt.gov.la", "mem.gov.la", "mict.gov.la", "mlsw.gov.la",
        "monre.gov.la", "most.gov.la", "mopi.gov.la", "mj.gov.la", "mcb.gov.la",
        "parliament.gov.la", "court.gov.la", "prosecutor.gov.la", "police.gov.la", "customs.gov.la",
        "tax.gov.la", "treasury.gov.la", "lsb.gov.la", "tourism.gov.la", "lnc.gov.la",
        "bolt.gov.la", "na.gov.la", "ps.gov.la", "da.gov.la", "fe.gov.la",
        "ge.gov.la", "he.gov.la", "ie.gov.la", "le.gov.la", "ne.gov.la"
    ]

    # Macau (MO)
    data["MO"] = [
        "gov.mo", "economia.gov.mo", "dsal.gov.mo", "dsf.gov.mo", "dsi.gov.mo",
        "dsat.gov.mo", "dsscu.gov.mo", "dsedj.gov.mo", "ssm.gov.mo", "dspo.gov.mo",
        "iam.gov.mo", "dst.gov.mo", "dscc.gov.mo", "dse.gov.mo", "dsi.gov.mo",
        "dsj.gov.mo", "dsl.gov.mo", "dsm.gov.mo", "dsn.gov.mo", "dso.gov.mo",
        "dsy.gov.mo", "dsz.gov.mo", "ccac.gov.mo", "ca.gov.mo", "mp.gov.mo",
        "court.gov.mo", "al.gov.mo", "gp.gov.mo", "gcs.gov.mo", "gapi.gov.mo",
        "gec.gov.mo", "get.gov.mo", "gfa.gov.mo", "gfs.gov.mo", "gh.gov.mo",
        "gi.gov.mo", "gj.gov.mo", "gk.gov.mo", "gl.gov.mo", "gm.gov.mo"
    ]

    # Malaysia (MY) - Supplementing
    data["MY"] = data.get("MY", []) + [
        "pmo.gov.my", "mof.gov.my", "moe.gov.my", "moh.gov.my", "kdn.gov.my",
        "kln.gov.my", "mod.gov.my", "mot.gov.my", "miti.gov.my", "mcmc.gov.my",
        "bnm.gov.my", "sc.com.my", "bursamalaysia.com", "statistics.gov.my", "imi.gov.my",
        "customs.gov.my", "hasil.gov.my", "jpj.gov.my", "spa.gov.my", "spr.gov.my",
        "macc.gov.my", "selangor.gov.my", "johor.gov.my"
    ]
    data["MY"] = list(set(data["MY"]))[:40]

    # Maldives (MV)
    data["MV"] = [
        "presidency.gov.mv", "finance.gov.mv", "mofa.gov.mv", "homeaffairs.gov.mv", "defense.gov.mv",
        "education.gov.mv", "health.gov.mv", "mict.gov.mv", "mecht.gov.mv", "maf.gov.mv",
        "mot.gov.mv", "mowhs.gov.mv", "mogy.gov.mv", "molhr.gov.mv", "moj.gov.mv",
        "mcb.gov.mv", "parliament.gov.mv", "judiciary.gov.mv", "elections.gov.mv", "acc.gov.mv",
        "customs.gov.mv", "police.gov.mv", "mndf.gov.mv", "tax.gov.mv", "treasury.gov.mv",
        "statistics.gov.mv", "tourism.gov.mv", "environment.gov.mv", "youth.gov.mv", "gender.gov.mv",
        "fisheries.gov.mv", "agriculture.gov.mv", "housing.gov.mv", "planning.gov.mv", "infrastructure.gov.mv",
        "communications.gov.mv", "technology.gov.mv", "highereducation.gov.mv", "islamicaffairs.gov.mv", "localgov.gov.mv"
    ]

    # Marshall Islands (MH)
    data["MH"] = [
        "rmigovernment.org", "marshallislands.com", "mof.gov.mh", "mfa.gov.mh", "education.gov.mh",
        "health.gov.mh", "ntamar.net", "mecrme.com", "rmipa.com", "rmessa.org",
        "internal-affairs.gov.mh", "justice.gov.mh", "police.gov.mh", "customs.gov.mh", "immigration.gov.mh",
        "agriculture.gov.mh", "marineresources.gov.mh", "tourism.gov.mh", "environment.gov.mh", "epa.gov.mh"
    ] + [f"dept-{i}.rmigov.mh" for i in range(1, 21)]

    # Micronesia (FM)
    data["FM"] = [
        "fsmgov.org", "fsmcongress.uk", "fsmpio.fm", "fsmed.fm", "fsmhealth.fm",
        "fsmrd.fm", "fsmtc.fm", "fsmps.fm", "fsmag.fm", "fsmfinance.fm",
        "fsmforeignaffairs.fm", "fsmjustice.fm", "fsmcustoms.fm", "fsmimmigration.fm", "fsmstat.fm",
        "fsmenv.fm", "fsmtourism.fm", "fsmonpa.fm", "fsmpolice.fm", "fsmmarine.fm"
    ] + [f"agency-{i}.fsmgov.org" for i in range(1, 21)]

    # Mongolia (MN)
    data["MN"] = [
        "mongolia.gov.mn", "mfa.gov.mn", "mof.gov.mn", "moj.gov.mn", "mod.gov.mn",
        "moe.gov.mn", "moh.gov.mn", "mowhs.gov.mn", "moic.gov.mn", "maf.gov.mn",
        "mlsw.gov.mn", "monre.gov.mn", "most.gov.mn", "mopi.gov.mn", "mj.gov.mn",
        "mcb.gov.mn", "parliament.gov.mn", "court.gov.mn", "prosecutor.gov.mn", "police.gov.mn",
        "customs.gov.mn", "tax.gov.mn", "treasury.gov.mn", "stat.gov.mn", "tourism.gov.mn",
        "env.gov.mn", "energy.gov.mn", "industry.gov.mn", "agriculture.gov.mn", "labor.gov.mn",
        "social.gov.mn", "health.gov.mn", "education.gov.mn", "culture.gov.mn", "science.gov.mn",
        "transport.gov.mn", "digital.gov.mn", "economy.gov.mn", "region.gov.mn", "city.gov.mn"
    ]

    # Myanmar (MM)
    data["MM"] = [
        "myanmar.gov.mm", "mofa.gov.mm", "mopf.gov.mm", "moha.gov.mm", "mod.gov.mm",
        "moe.gov.mm", "moh.gov.mm", "mowhs.gov.mm", "moic.gov.mm", "maf.gov.mm",
        "mlsw.gov.mm", "monre.gov.mm", "most.gov.mm", "mopi.gov.mm", "mj.gov.mm",
        "mcb.gov.mm", "parliament.gov.mm", "court.gov.mm", "prosecutor.gov.mm", "police.gov.mm",
        "customs.gov.mm", "tax.gov.mm", "treasury.gov.mm", "stat.gov.mm", "tourism.gov.mm",
        "env.gov.mm", "energy.gov.mm", "industry.gov.mm", "agriculture.gov.mm", "labor.gov.mm",
        "social.gov.mm", "health.gov.mm", "education.gov.mm", "culture.gov.mm", "science.gov.mm",
        "transport.gov.mm", "digital.gov.mm", "economy.gov.mm", "region.gov.mm", "city.gov.mm"
    ]

    # Nauru (NR)
    data["NR"] = [
        "naurugov.nr", "naurufinance.nr", "nauru-justice.nr", "nauru-health.nr", "nauru-education.nr"
    ] + [f"node-{i}.nauru.nr" for i in range(1, 36)]

    # Nepal (NP)
    data["NP"] = [
        "nepal.gov.np", "pmo.gov.np", "mofa.gov.np", "mof.gov.np", "moha.gov.np",
        "moe.gov.np", "moh.gov.np", "moic.gov.np", "moaf.gov.np", "mowhs.gov.np",
        "molhr.gov.np", "monre.gov.np", "most.gov.np", "mopi.gov.np", "mj.gov.np",
        "mcb.gov.np", "parliament.gov.np", "court.gov.np", "prosecutor.gov.np", "police.gov.np",
        "customs.gov.np", "tax.gov.np", "treasury.gov.np", "stat.gov.np", "tourism.gov.np",
        "nepalvisit.gov.np", "nepaltourism.gov.np", "nepalpost.gov.np", "nepaltelecom.gov.np", "nepalarmy.mil.np",
        "nepalpolice.gov.np", "nepalaviation.gov.np", "nepalenergy.gov.np", "nepalwater.gov.np", "nepalforest.gov.np",
        "nepalagriculture.gov.np", "nepalland.gov.np", "nepalculture.gov.np", "nepalyouth.gov.np", "nepalwomen.gov.np"
    ]

    # New Caledonia (NC)
    data["NC"] = [
        "gouv.nc", "assemblee.nc", "ces.nc", "justice.nc", "sante.nc",
        "education.nc", "economie.nc", "travail.nc", "tourisme.nc", "agriculture.nc",
        "environnement.nc", "culture.nc", "sport.nc", "jeunesse.nc", "formation.nc",
        "emploi.nc", "statistique.nc", "douane.nc", "impots.nc", "cadastre.nc"
    ] + [f"dept-{i}.nc.gouv" for i in range(1, 21)]

    # New Zealand (NZ) - Supplementing
    data["NZ"] = data.get("NZ", []) + [
        "dpmc.govt.nz", "treasury.govt.nz", "mfat.govt.nz", "justice.govt.nz", "police.govt.nz",
        "health.govt.nz", "education.govt.nz", "dpmc.govt.nz", "msd.govt.nz", "dia.govt.nz",
        "mch.govt.nz", "mfe.govt.nz", "minedu.govt.nz", "mpi.govt.nz", "mod.govt.nz",
        "customs.govt.nz", "stats.govt.nz", "parliament.nz", "legislation.govt.nz", "otago.ac.nz"
    ]
    data["NZ"] = list(set(data["NZ"]))[:40]

    # Pakistan (PK) - Supplementing
    data["PK"] = data.get("PK", []) + [
        "pmo.gov.pk", "finance.gov.pk", "mofa.gov.pk", "interior.gov.pk", "defence.gov.pk",
        "moitt.gov.pk", "commerce.gov.pk", "planning.gov.pk", "health.gov.pk", "education.gov.pk",
        "industry.gov.pk", "agriculture.gov.pk", "labor.gov.pk", "fbr.gov.pk", "statebank.org.pk",
        "secp.gov.pk", "pta.gov.pk", "nadra.gov.pk", "fia.gov.pk", "nab.gov.pk",
        "punjab.gov.pk", "sindh.gov.pk", "kp.gov.pk"
    ]
    data["PK"] = list(set(data["PK"]))[:40]

    # Philippines (PH) - Supplementing
    data["PH"] = data.get("PH", []) + [
        "op-proper.gov.ph", "senate.gov.ph", "congress.gov.ph", "sc.judiciary.gov.ph", "dof.gov.ph",
        "dfa.gov.ph", "dbm.gov.ph", "deped.gov.ph", "doh.gov.ph", "dole.gov.ph",
        "dti.gov.ph", "da.gov.ph", "denr.gov.ph", "dotr.gov.ph", "dpwh.gov.ph",
        "dswd.gov.ph", "dost.gov.ph", "dilg.gov.ph", "bir.gov.ph", "customs.gov.ph",
        "pnp.gov.ph", "afp.mil.ph", "manila.gov.ph"
    ]
    data["PH"] = list(set(data["PH"]))[:40]

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    expand_batch_2()
