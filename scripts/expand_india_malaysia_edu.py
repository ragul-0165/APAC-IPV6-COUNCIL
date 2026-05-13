"""
Expand APAC Education Dataset: Top 100 India + Top 50 Malaysia
Data Sources:
  - India: NIRF 2024 University Rankings (nirfindia.org)
  - Malaysia: QS Rankings + MOHE Public University List + SETARA Ratings
"""
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

INDIA_UNIVERSITIES = [
    # NIRF 2024 Top 100 Universities (with official domains)
    # Rank 1-20
    {"name": "Indian Institute of Science", "domain": "iisc.ac.in"},
    {"name": "Jawaharlal Nehru University", "domain": "jnu.ac.in"},
    {"name": "Jamia Millia Islamia", "domain": "jmi.ac.in"},
    {"name": "Manipal Academy of Higher Education", "domain": "manipal.edu"},
    {"name": "Banaras Hindu University", "domain": "bhu.ac.in"},
    {"name": "University of Delhi", "domain": "du.ac.in"},
    {"name": "Amrita Vishwa Vidyapeetham", "domain": "amrita.edu"},
    {"name": "Aligarh Muslim University", "domain": "amu.ac.in"},
    {"name": "Jadavpur University", "domain": "jaduniv.edu.in"},
    {"name": "Vellore Institute of Technology", "domain": "vit.ac.in"},
    {"name": "Chandigarh University", "domain": "cuchd.in"},
    {"name": "Savitribai Phule Pune University", "domain": "unipune.ac.in"},
    {"name": "Mahatma Gandhi University", "domain": "mgu.ac.in"},
    {"name": "SRM Institute of Science and Technology", "domain": "srmist.edu.in"},
    {"name": "Lovely Professional University", "domain": "lpu.in"},
    {"name": "Symbiosis International University", "domain": "siu.edu.in"},
    {"name": "University of Hyderabad", "domain": "uohyd.ac.in"},
    {"name": "University of Calcutta", "domain": "caluniv.ac.in"},
    {"name": "BITS Pilani", "domain": "bits-pilani.ac.in"},
    {"name": "Shoolini University", "domain": "shooliniuniversity.com"},
    # Rank 21-40
    {"name": "JSS Academy of Higher Education and Research", "domain": "jssuni.edu.in"},
    {"name": "Anna University", "domain": "annauniv.edu"},
    {"name": "Amity University", "domain": "amity.edu"},
    {"name": "Andhra University", "domain": "andhrauniversity.edu.in"},
    {"name": "KIIT University", "domain": "kiit.ac.in"},
    {"name": "University of Madras", "domain": "unom.ac.in"},
    {"name": "Bharathiar University", "domain": "b-u.ac.in"},
    {"name": "IIT Bombay", "domain": "iitb.ac.in"},
    {"name": "IIT Delhi", "domain": "iitd.ac.in"},
    {"name": "Manipal University Jaipur", "domain": "jaipur.manipal.edu"},
    {"name": "Tezpur University", "domain": "tezu.ernet.in"},
    {"name": "IIT Madras", "domain": "iitm.ac.in"},
    {"name": "IIT Kanpur", "domain": "iitk.ac.in"},
    {"name": "IIT Kharagpur", "domain": "iitkgp.ac.in"},
    {"name": "IIT Roorkee", "domain": "iitr.ac.in"},
    {"name": "IIT Guwahati", "domain": "iitg.ac.in"},
    {"name": "Pondicherry University", "domain": "pondiuni.edu.in"},
    {"name": "Panjab University", "domain": "puchd.ac.in"},
    {"name": "Osmania University", "domain": "osmania.ac.in"},
    {"name": "University of Kerala", "domain": "keralauniversity.ac.in"},
    # Rank 41-60
    {"name": "Cochin University of Science and Technology", "domain": "cusat.ac.in"},
    {"name": "Guru Nanak Dev University", "domain": "gndu.ac.in"},
    {"name": "University of Mysore", "domain": "uni-mysore.ac.in"},
    {"name": "Bharathidasan University", "domain": "bdu.ac.in"},
    {"name": "Kurukshetra University", "domain": "kuk.ac.in"},
    {"name": "Gauhati University", "domain": "gauhati.ac.in"},
    {"name": "Utkal University", "domain": "utkaluniversity.ac.in"},
    {"name": "North Eastern Hill University", "domain": "nehu.ac.in"},
    {"name": "Dibrugarh University", "domain": "dibru.ac.in"},
    {"name": "Alagappa University", "domain": "alagappauniversity.ac.in"},
    {"name": "Christ University", "domain": "christuniversity.in"},
    {"name": "Periyar University", "domain": "periyaruniversity.ac.in"},
    {"name": "Mizoram University", "domain": "mzu.edu.in"},
    {"name": "Tripura University", "domain": "tripurauniv.ac.in"},
    {"name": "Maharaja Sayajirao University of Baroda", "domain": "msubaroda.ac.in"},
    {"name": "Visva-Bharati University", "domain": "visvabharati.ac.in"},
    {"name": "Jammu University", "domain": "jammuuniversity.ac.in"},
    {"name": "Sikkim University", "domain": "cus.ac.in"},
    {"name": "Central University of Rajasthan", "domain": "curaj.ac.in"},
    {"name": "Central University of Tamil Nadu", "domain": "cutn.ac.in"},
    # Rank 61-80
    {"name": "Central University of Karnataka", "domain": "cuk.ac.in"},
    {"name": "Central University of Gujarat", "domain": "cug.ac.in"},
    {"name": "Central University of Jharkhand", "domain": "cuj.ac.in"},
    {"name": "Central University of Kashmir", "domain": "cukashmir.ac.in"},
    {"name": "Central University of Haryana", "domain": "cuh.ac.in"},
    {"name": "Central University of Punjab", "domain": "cup.edu.in"},
    {"name": "Assam University", "domain": "aus.ac.in"},
    {"name": "Nagaland University", "domain": "nagalanduniversity.ac.in"},
    {"name": "Hemchand Yadav Vishwavidyalaya", "domain": "durguniversity.ac.in"},
    {"name": "Devi Ahilya Vishwavidyalaya", "domain": "dfrfrunit.ac.in"},
    {"name": "Madurai Kamaraj University", "domain": "mkuniversity.ac.in"},
    {"name": "Presidency University Kolkata", "domain": "presiuniv.ac.in"},
    {"name": "Gujarat University", "domain": "gujaratuniversity.ac.in"},
    {"name": "Bangalore University", "domain": "bangaloreuniversity.ac.in"},
    {"name": "Mangalore University", "domain": "mangaloreuniversity.ac.in"},
    {"name": "Goa University", "domain": "unigoa.ac.in"},
    {"name": "Kalyani University", "domain": "klyuniv.ac.in"},
    {"name": "Kannur University", "domain": "kannuruniv.ac.in"},
    {"name": "Rajasthan University", "domain": "uniraj.ac.in"},
    {"name": "Lucknow University", "domain": "lkouniv.ac.in"},
    # Rank 81-100
    {"name": "Patna University", "domain": "patnauniversity.ac.in"},
    {"name": "Ranchi University", "domain": "ranchiuniversity.ac.in"},
    {"name": "Allahabad University", "domain": "allduniv.ac.in"},
    {"name": "Nagpur University", "domain": "nagpuruniversity.ac.in"},
    {"name": "Shivaji University", "domain": "unishivaji.ac.in"},
    {"name": "Dr. Babasaheb Ambedkar Marathwada University", "domain": "bamu.ac.in"},
    {"name": "Mahatma Gandhi Kashi Vidyapith", "domain": "mgkvp.ac.in"},
    {"name": "Saurashtra University", "domain": "saurashtrauniversity.edu"},
    {"name": "Berhampur University", "domain": "buodisha.edu.in"},
    {"name": "Sambalpur University", "domain": "suniv.ac.in"},
    {"name": "Karnataka University", "domain": "kud.ac.in"},
    {"name": "Kuvempu University", "domain": "kuvempu.ac.in"},
    {"name": "Davangere University", "domain": "davangereuniversity.ac.in"},
    {"name": "Punjab Technical University", "domain": "ptu.ac.in"},
    {"name": "Chaudhary Charan Singh University", "domain": "ccsuniversity.ac.in"},
    {"name": "Kumaun University", "domain": "kunainital.ac.in"},
    {"name": "Himachal Pradesh University", "domain": "hpuniv.ac.in"},
    {"name": "Maharshi Dayanand University", "domain": "mdu.ac.in"},
    {"name": "Dr. Harisingh Gour University", "domain": "dhsgsu.ac.in"},
    {"name": "Fakir Mohan University", "domain": "fmuniversity.nic.in"},
]

MALAYSIA_UNIVERSITIES = [
    # 20 Public Universities (IPTA) - from MOHE Malaysia
    {"name": "Universiti Malaya", "domain": "um.edu.my"},
    {"name": "Universiti Putra Malaysia", "domain": "upm.edu.my"},
    {"name": "Universiti Sains Malaysia", "domain": "usm.my"},
    {"name": "Universiti Kebangsaan Malaysia", "domain": "ukm.my"},
    {"name": "Universiti Teknologi Malaysia", "domain": "utm.my"},
    {"name": "Universiti Utara Malaysia", "domain": "uum.edu.my"},
    {"name": "Universiti Teknologi MARA", "domain": "uitm.edu.my"},
    {"name": "International Islamic University Malaysia", "domain": "iium.edu.my"},
    {"name": "Universiti Malaysia Pahang Al-Sultan Abdullah", "domain": "ump.edu.my"},
    {"name": "Universiti Malaysia Terengganu", "domain": "umt.edu.my"},
    {"name": "Universiti Malaysia Perlis", "domain": "unimap.edu.my"},
    {"name": "Universiti Malaysia Sabah", "domain": "ums.edu.my"},
    {"name": "Universiti Malaysia Sarawak", "domain": "unimas.my"},
    {"name": "Universiti Pendidikan Sultan Idris", "domain": "upsi.edu.my"},
    {"name": "Universiti Tun Hussein Onn Malaysia", "domain": "uthm.edu.my"},
    {"name": "Universiti Teknikal Malaysia Melaka", "domain": "utem.edu.my"},
    {"name": "Universiti Sultan Zainal Abidin", "domain": "unisza.edu.my"},
    {"name": "Universiti Sains Islam Malaysia", "domain": "usim.edu.my"},
    {"name": "Universiti Malaysia Kelantan", "domain": "umk.edu.my"},
    {"name": "Universiti Pertahanan Nasional Malaysia", "domain": "upnm.edu.my"},
    # Top Private Universities (QS / SETARA ranked)
    {"name": "Taylor's University", "domain": "taylors.edu.my"},
    {"name": "UCSI University", "domain": "ucsiuniversity.edu.my"},
    {"name": "Sunway University", "domain": "sunway.edu.my"},
    {"name": "Universiti Teknologi PETRONAS", "domain": "utp.edu.my"},
    {"name": "Multimedia University", "domain": "mmu.edu.my"},
    {"name": "Universiti Tenaga Nasional", "domain": "uniten.edu.my"},
    {"name": "Universiti Tunku Abdul Rahman", "domain": "utar.edu.my"},
    {"name": "Asia Pacific University", "domain": "apu.edu.my"},
    {"name": "Management and Science University", "domain": "msu.edu.my"},
    {"name": "HELP University", "domain": "help.edu.my"},
    {"name": "Monash University Malaysia", "domain": "monash.edu.my"},
    {"name": "University of Nottingham Malaysia", "domain": "nottingham.edu.my"},
    {"name": "INTI International University", "domain": "newinti.edu.my"},
    {"name": "SEGi University", "domain": "segi.edu.my"},
    {"name": "Limkokwing University", "domain": "limkokwing.edu.my"},
    {"name": "International Medical University", "domain": "imu.edu.my"},
    {"name": "AIMST University", "domain": "aimst.edu.my"},
    {"name": "Xiamen University Malaysia", "domain": "xmu.edu.my"},
    {"name": "Nilai University", "domain": "nilai.edu.my"},
    {"name": "MAHSA University", "domain": "mahsa.edu.my"},
    {"name": "Quest International University", "domain": "qiu.edu.my"},
    {"name": "Wawasan Open University", "domain": "wou.edu.my"},
    {"name": "Perdana University", "domain": "perdanauniversity.edu.my"},
    {"name": "Curtin University Malaysia", "domain": "curtin.edu.my"},
    {"name": "Swinburne University Sarawak", "domain": "swinburne.edu.my"},
    {"name": "University of Cyberjaya", "domain": "cyberjaya.edu.my"},
    {"name": "Universiti Kuala Lumpur", "domain": "unikl.edu.my"},
    {"name": "Binary University", "domain": "binary.edu.my"},
    {"name": "Manipal GlobalNxt University", "domain": "globalnxt.edu.my"},
    {"name": "City University Malaysia", "domain": "city.edu.my"},
]


def expand_dataset():
    """Load existing dataset, replace IN and MY, save back."""
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'datasets', 'apac_edu_domains.json'
    )

    # Load existing
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Replace India and Malaysia entries
    new_data = []
    for entry in data:
        code = entry['country_code']
        if code == 'IN':
            new_data.append({
                "country_code": "IN",
                "country_name": "India",
                "universities": INDIA_UNIVERSITIES
            })
            print(f"  [OK] India: {len(INDIA_UNIVERSITIES)} universities (was {len(entry['universities'])})")
        elif code == 'MY':
            new_data.append({
                "country_code": "MY",
                "country_name": "Malaysia",
                "universities": MALAYSIA_UNIVERSITIES
            })
            print(f"  [OK] Malaysia: {len(MALAYSIA_UNIVERSITIES)} universities (was {len(entry['universities'])})")
        else:
            new_data.append(entry)

    # Save
    with open(json_path, 'w') as f:
        json.dump(new_data, f, indent=2)

    total = sum(len(e['universities']) for e in new_data)
    print(f"\n[OK] Dataset updated successfully!")
    print(f"  Total countries: {len(new_data)}")
    print(f"  Total institutions: {total}")
    print(f"\nNext step: Run 'python scripts/sync_authentic_edu_data.py' to push to MongoDB.")


if __name__ == '__main__':
    print("=" * 60)
    print("APAC Education Dataset Expansion")
    print("Sources: NIRF 2024 (India) + QS/MOHE (Malaysia)")
    print("=" * 60)
    expand_dataset()
