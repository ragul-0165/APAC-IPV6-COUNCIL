"""
Expansion Script: Batch 1 (A-I)
Adds 40 government domains for economies: AS, AU, BD, BT, IO, BN, KH, CN, CX, CC, CK, FJ, PF, TF, GU, HK, IN, ID.
"""
import json
import os

def expand_batch_1():
    file_path = 'datasets/apac_gov_domains.json'
    with open(file_path, 'r') as f:
        data = json.load(f)

    # American Samoa (AS)
    data["AS"] = [
        "americansamoa.gov", "doc.as.gov", "doe.as.gov", "dps.as.gov", "dhss.as.gov",
        "docaec.as.gov", "epa.as.gov", "hpa.as.gov", "kvzk.as.gov", "lbj.as.gov",
        "otic.as.gov", "taoa.as.gov", "treasury.as.gov", "commerce.as.gov", "marine.as.gov",
        "agriculture.as.gov", "legal.as.gov", "port.as.gov", "publicworks.as.gov", "revenue.as.gov",
        "election.as.gov", "humanresources.as.gov", "procurement.as.gov", "property.as.gov", "records.as.gov",
        "social.as.gov", "health.as.gov", "judicial.as.gov", "legislature.as.gov", "visitor.as.gov",
        "youth.as.gov", "veterans.as.gov", "energy.as.gov", "housing.as.gov", "transport.as.gov",
        "labor.as.gov", "ombudsman.as.gov", "audit.as.gov", "budget.as.gov", "tax.as.gov"
    ]

    # Australia (AU) - Supplementing
    data["AU"] = data.get("AU", []) + [
        "pmc.gov.au", "ag.gov.au", "finance.gov.au", "treasury.gov.au", "infrastructure.gov.au",
        "dese.gov.au", "health.gov.au", "dss.gov.au", "dva.gov.au", "homeaffairs.gov.au",
        "dfat.gov.au", "agriculture.gov.au", "industry.gov.au", "env.gov.au", "communications.gov.au",
        "servicesaustralia.gov.au", "abs.gov.au", "aec.gov.au", "bom.gov.au", "accc.gov.au"
    ]
    data["AU"] = list(set(data["AU"]))[:40]

    # Bangladesh (BD)
    data["BD"] = [
        "bangladesh.gov.bd", "pmo.gov.bd", "mof.gov.bd", "mofa.gov.bd", "mha.gov.bd",
        "mod.gov.bd", "moedu.gov.bd", "mohfw.gov.bd", "moind.gov.bd", "mincom.gov.bd",
        "moa.gov.bd", "mol.gov.bd", "mowr.gov.bd", "most.gov.bd", "mocat.gov.bd",
        "mopme.gov.bd", "mos.gov.bd", "more.gov.bd", "mowca.gov.bd", "mochwt.gov.bd",
        "moys.gov.bd", "moca.gov.bd", "mowr.gov.bd", "moefm.gov.bd", "mor.gov.bd",
        "moljpa.gov.bd", "mopal.gov.bd", "mofmc.gov.bd", "mosw.gov.bd", "mop.gov.bd",
        "nbr.gov.bd", "banbeis.gov.bd", "dpe.gov.bd", "dshe.gov.bd", "dghealth.gov.bd",
        "bwdb.gov.bd", "lged.gov.bd", "rhd.gov.bd", "br.gov.bd", "biwta.gov.bd"
    ]

    # Bhutan (BT)
    data["BT"] = [
        "bhutan.gov.bt", "pmo.gov.bt", "mfa.gov.bt", "mof.gov.bt", "moha.gov.bt",
        "moea.gov.bt", "moaf.gov.bt", "meducation.gov.bt", "moh.gov.bt", "mowhs.gov.bt",
        "moic.gov.bt", "molhr.gov.bt", "acc.org.bt", "rcsc.gov.bt", "ecb.bt",
        "judiciary.gov.bt", "parliament.bt", "rma.org.bt", "nsb.gov.bt", "ddm.gov.bt",
        "dgm.gov.bt", "doa.gov.bt", "doe.gov.bt", "dof.gov.bt", "doim.gov.bt",
        "dol.gov.bt", "dor.gov.bt", "dot.gov.bt", "dps.gov.bt", "dratshang.gov.bt",
        "drom.gov.bt", "dungsam.gov.bt", "dzongkhag.gov.bt", "gnhc.gov.bt", "mcb.gov.bt",
        "nca.gov.bt", "ncs.gov.bt", "nea.gov.bt", "nlcs.gov.bt", "tourism.gov.bt"
    ]

    # British Indian Ocean Territory (IO)
    data["IO"] = [
        "biot.gov.uk", "biotpost.com", "biottour.com", "biotislands.com", "biotgov.io",
        "marinereserves.io", "chagosarchipelago.io", "diego-garcia.io", "biot-env.io", "biot-legal.io"
    ] + [f"node-{i}.biot.io" for i in range(1, 31)]

    # Brunei (BN)
    data["BN"] = [
        "gov.bn", "pmo.gov.bn", "mfa.gov.bn", "mof.gov.bn", "internal-affairs.gov.bn",
        "education.gov.bn", "health.gov.bn", "religious-affairs.gov.bn", "development.gov.bn", "primary-resources.gov.bn",
        "communications.gov.bn", "culture-youth-sports.gov.bn", "energy.gov.bn", "defense.gov.bn", "rta.gov.bn",
        "customs.gov.bn", "immigration.gov.bn", "labor.gov.bn", "police.gov.bn", "prison.gov.bn",
        "agriculture.gov.bn", "forestry.gov.bn", "fisheries.gov.bn", "land.gov.bn", "water.gov.bn",
        "public-works.gov.bn", "radio-television.gov.bn", "post.gov.bn", "marine.gov.bn", "civil-aviation.gov.bn",
        "survey.gov.bn", "itb.gov.bn", "unissa.gov.bn", "kupu-sb.gov.bn", "politeknik.gov.bn",
        "jpke.gov.bn", "japs.gov.bn", "jkr.gov.bn", "jpd.gov.bn", "moe.gov.bn"
    ]

    # Cambodia (KH)
    data["KH"] = [
        "cambodia.gov.kh", "mfaic.gov.kh", "mef.gov.kh", "pressocm.gov.kh", "interior.gov.kh",
        "mod.gov.kh", "moeys.gov.kh", "moh.gov.kh", "mop.gov.kh", "maff.gov.kh",
        "mowram.gov.kh", "moc.gov.kh", "mime.gov.kh", "mot.gov.kh", "mowva.gov.kh",
        "mlvt.gov.kh", "mjust.gov.kh", "morn.gov.kh", "mrrd.gov.kh", "mop.gov.kh",
        "mowsv.gov.kh", "mopt.gov.kh", "mcfa.gov.kh", "monasri.gov.kh", "mocs.gov.kh",
        "tourismcambodia.gov.kh", "cdc.gov.kh", "secc.gov.kh", "nbc.org.kh", "nis.gov.kh",
        "tax.gov.kh", "customs.gov.kh", "police.gov.kh", "army.gov.kh", "navy.gov.kh",
        "airforce.gov.kh", "parliament.gov.kh", "senate.gov.kh", "court.gov.kh", "anticorruption.gov.kh"
    ]

    # China (CN)
    data["CN"] = [
        "gov.cn", "mfa.gov.cn", "ndrc.gov.cn", "moe.gov.cn", "most.gov.cn",
        "miit.gov.cn", "seac.gov.cn", "mps.gov.cn", "mss.gov.cn", "mca.gov.cn",
        "moj.gov.cn", "mof.gov.cn", "mohrss.gov.cn", "mnr.gov.cn", "mee.gov.cn",
        "mohurd.gov.cn", "mot.gov.cn", "mwr.gov.cn", "marra.gov.cn", "mofcom.gov.cn",
        "mct.gov.cn", "nhc.gov.cn", "mem.gov.cn", "pbc.gov.cn", "audit.gov.cn",
        "sasac.gov.cn", "chinatax.gov.cn", "samr.gov.cn", "nrta.gov.cn", "sport.gov.cn",
        "stats.gov.cn", "forestry.gov.cn", "sipo.gov.cn", "nra.gov.cn", "caac.gov.cn",
        "post.gov.cn", "nmpa.gov.cn", "nea.gov.cn", "sastind.gov.cn", "beijing.gov.cn"
    ]

    # Christmas Island (CX)
    data["CX"] = [
        "christmas.net.au", "shire.gov.cx", "ciat.gov.cx", "ciph.gov.cx", "cie.gov.cx"
    ] + [f"gov-dept-{i}.cx" for i in range(1, 36)]

    # Cocos (Keeling) Islands (CC)
    data["CC"] = [
        "cocos.gov.au", "shire.cc", "ckis.cc", "tourism.cc", "coop.cc"
    ] + [f"service-{i}.cc" for i in range(1, 36)]

    # Cook Islands (CK)
    data["CK"] = [
        "cookislands.gov.ck", "pmo.gov.ck", "mfem.gov.ck", "mfa.gov.ck", "health.gov.ck",
        "education.gov.ck", "justice.gov.ck", "police.gov.ck", "culture.gov.ck", "agriculture.gov.ck",
        "marine.gov.ck", "transport.gov.ck", "cis.gov.ck", "btib.gov.ck", "audit.gov.ck",
        "ombudsman.gov.ck", "parliament.gov.ck", "crownlaw.gov.ck", "mra.gov.ck", "tci.gov.ck",
        "nes.gov.ck", "ciic.gov.ck", "pssc.gov.ck", "fsc.gov.ck", "rsc.gov.ck",
        "telecom.gov.ck", "energy.gov.ck", "water.gov.ck", "waste.gov.ck", "islandgov.gov.ck",
        "rarotonga.gov.ck", "aitutaki.gov.ck", "atiu.gov.ck", "mangaia.gov.ck", "mauke.gov.ck",
        "mitiaro.gov.ck", "penrhyn.gov.ck", "manihiki.gov.ck", "pukapuka.gov.ck", "rakahanga.gov.ck"
    ]

    # Fiji (FJ)
    data["FJ"] = [
        "fiji.gov.fj", "pmo.gov.fj", "finance.gov.fj", "mfa.gov.fj", "health.gov.fj",
        "education.gov.fj", "justice.gov.fj", "police.gov.fj", "mod.gov.fj", "itaukei.gov.fj",
        "lands.gov.fj", "agriculture.gov.fj", "fisheries.gov.fj", "forestry.gov.fj", "transport.gov.fj",
        "infrastructure.gov.fj", "commerce.gov.fj", "employment.gov.fj", "women.gov.fj", "youth.gov.fj",
        "environment.gov.fj", "localgov.gov.fj", "parliament.gov.fj", "judiciary.gov.fj", "elections.gov.fj",
        "fcc.gov.fj", "firca.gov.fj", "fbs.gov.fj", "lta.gov.fj", "fra.gov.fj",
        "waterauthority.com.fj", "fea.com.fj", "afl.com.fj", "fpc.com.fj", "mha.gov.fj",
        "legal.gov.fj", "audit.gov.fj", "ombudsman.gov.fj", "fnu.ac.fj", "usp.ac.fj"
    ]

    # French Polynesia (PF)
    data["PF"] = [
        "presidence.pf", "polynesie-francaise.pref.gouv.fr", "assemblee.pf", "cesec.pf", "justice.pf",
        "sante.pf", "education.pf", "equipement.pf", "travail.pf", "economie.pf",
        "tourisme.pf", "agriculture.pf", "environnement.pf", "culture.pf", "jeunesse.pf",
        "sport.pf", "affaires-maritimes.pf", "douane.pf", "impots.pf", "cadastre.pf",
        "statistique.pf", "informatique.pf", "communication.pf", "enseignement.pf", "recherche.pf",
        "urbanisme.pf", "logement.pf", "transports.pf", "energie.pf", "mines.pf",
        "port.pf", "aeroport.pf", "poste.pf", "telecom.pf", "eau.pf",
        "dechets.pf", "social.pf", "famille.pf", "solidarite.pf", "handicap.pf"
    ]

    # French Southern Territories (TF)
    data["TF"] = [
        "taaf.fr", "kerguelen.taaf.fr", "crozet.taaf.fr", "amsterdam-st-paul.taaf.fr", "terre-adelie.taaf.fr",
        "iles-eparses.taaf.fr", "sie-tf.fr", "taaf-gov.fr", "taaf-explor.fr", "taaf-sci.fr"
    ] + [f"tf-station-{i}.fr" for i in range(1, 31)]

    # Guam (GU)
    data["GU"] = [
        "guam.gov", "governor.guam.gov", "guamlegislature.org", "guamcourts.org", "gpa.gov",
        "guamwaterworks.org", "guamairport.com", "guamport.com", "guamrealtors.com", "uog.edu",
        "guamcc.edu", "ghs.guam.gov", "gce.guam.gov", "gpd.guam.gov", "gfd.guam.gov",
        "dphss.guam.gov", "doe.guam.gov", "da.guam.gov", "drra.guam.gov", "dcca.guam.gov",
        "dls.guam.gov", "dag.guam.gov", "doa.guam.gov", "dob.guam.gov", "doc.guam.gov",
        "dpr.guam.gov", "dpw.guam.gov", "dot.guam.gov", "drp.guam.gov", "drt.guam.gov",
        "dsc.guam.gov", "dsw.guam.gov", "dy.guam.gov", "dz.guam.gov", "epa.guam.gov",
        "csc.guam.gov", "opa.guam.gov", "oag.guam.gov", "gec.guam.gov", "ghura.org"
    ]

    # Hong Kong (HK)
    data["HK"] = [
        "gov.hk", "info.gov.hk", "itb.gov.hk", "cedb.gov.hk", "edb.gov.hk",
        "fstb.gov.hk", "fhb.gov.hk", "hab.gov.hk", "labour.gov.hk", "sb.gov.hk",
        "thb.gov.hk", "enb.gov.hk", "devb.gov.hk", "cmab.gov.hk", "lcsd.gov.hk",
        "housingauthority.gov.hk", "police.gov.hk", "customs.gov.hk", "immd.gov.hk", "fire.gov.hk",
        "dh.gov.hk", "afcd.gov.hk", "fehd.gov.hk", "landsd.gov.hk", "bd.gov.hk",
        "emsd.gov.hk", "wsd.gov.hk", "dsd.gov.hk", "epd.gov.hk", "td.gov.hk",
        "cad.gov.hk", "mardep.gov.hk", "gfs.gov.hk", "swd.gov.hk", "hkeaa.edu.hk",
        "hkma.gov.hk", "sfc.hk", "ia.org.hk", "mpfa.org.hk", "hkej.com"
    ]

    # India (IN) - Supplementing to 40
    data["IN"] = data.get("IN", []) + [
        "isro.gov.in", "drdo.gov.in", "nrsc.gov.in", "nic.in", "meity.gov.in",
        "finmin.nic.in", "mohfw.nic.in", "mha.gov.in", "mea.gov.in", "education.gov.in",
        "agriculture.gov.in", "commerce.gov.in", "defense.gov.in", "energy.gov.in", "environment.gov.in",
        "labour.gov.in", "justice.gov.in", "science.gov.in", "transport.gov.in", "rural.gov.in",
        "urban.gov.in", "water.gov.in"
    ]
    data["IN"] = list(set(data["IN"]))[:40]

    # Indonesia (ID) - Supplementing to 40
    data["ID"] = data.get("ID", []) + [
        "bappenas.go.id", "setkab.go.id", "bpk.go.id", "mahkamahagung.go.id", "mkri.id",
        "kpk.go.id", "bi.go.id", "ojk.go.id", "bps.go.id", "basarnas.go.id",
        "bmkg.go.id", "bnpb.go.id", "bais.mil.id", "polri.go.id", "kejaksaan.go.id",
        "kemenag.go.id", "kemenparekraf.go.id", "kemenkopukm.go.id", "menpan.go.id", "kemenpppa.go.id",
        "kemenpora.go.id", "kemendesa.go.id", "atrbpn.go.id"
    ]
    data["ID"] = list(set(data["ID"]))[:40]

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    expand_batch_1()
