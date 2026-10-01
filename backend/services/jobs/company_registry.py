from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Company:
    slug: str
    name: str
    category: str
    website_url: str
    careers_url: str
    logo_url: str
    priority: int


TARGET_COMPANIES = (
    Company("accenture", "Accenture", "mnc", "https://www.accenture.com/", "https://www.accenture.com/in-en/careers", "https://www.accenture.com/content/dam/accenture/final/accenture-com/images/careers/accenture-logo.png", 10),
    Company("cognizant", "Cognizant", "mnc", "https://www.cognizant.com/", "https://careers.cognizant.com/", "https://upload.wikimedia.org/wikipedia/commons/4/43/Cognizant_logo_2022.svg", 10),
    Company("infosys", "Infosys", "mnc", "https://www.infosys.com/", "https://www.infosys.com/careers/", "https://upload.wikimedia.org/wikipedia/commons/9/95/Infosys_logo.svg", 10),
    Company("tcs", "Tata Consultancy Services", "mnc", "https://www.tcs.com/", "https://www.tcs.com/careers", "https://upload.wikimedia.org/wikipedia/commons/b/b1/Tata_Consultancy_Services_Logo.svg", 10),
    Company("wipro", "Wipro", "mnc", "https://www.wipro.com/", "https://careers.wipro.com/", "https://upload.wikimedia.org/wikipedia/commons/a/a0/Wipro_Primary_Logo_Color_RGB.svg", 10),
    Company("capgemini", "Capgemini", "mnc", "https://www.capgemini.com/", "https://www.capgemini.com/careers/", "https://upload.wikimedia.org/wikipedia/commons/9/9d/Capgemini_201x_logo.svg", 20),
    Company("ibm", "IBM", "mnc", "https://www.ibm.com/", "https://www.ibm.com/careers/", "https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg", 10),
    Company("deloitte", "Deloitte", "mnc", "https://www.deloitte.com/", "https://www.deloitte.com/global/en/careers.html", "https://upload.wikimedia.org/wikipedia/commons/5/56/Deloitte.svg", 20),
    Company("ey", "EY", "mnc", "https://www.ey.com/", "https://www.ey.com/en_in/careers/job-search", "https://upload.wikimedia.org/wikipedia/commons/3/34/EY_logo_2019.svg", 20),
    Company("kpmg", "KPMG", "mnc", "https://kpmg.com/", "https://kpmg.com/in/en/home/careers.html", "https://upload.wikimedia.org/wikipedia/commons/9/9d/KPMG_logo.svg", 20),
    Company("pwc", "PwC", "mnc", "https://www.pwc.com/", "https://www.pwc.in/careers.html", "https://upload.wikimedia.org/wikipedia/commons/0/0e/PricewaterhouseCoopers_Logo.svg", 20),
    Company("hcltech", "HCLTech", "mnc", "https://www.hcltech.com/", "https://careers.hcltech.com/", "https://upload.wikimedia.org/wikipedia/commons/3/39/HCL_Technologies_logo.svg", 20),
    Company("tech-mahindra", "Tech Mahindra", "mnc", "https://www.techmahindra.com/", "https://careers.techmahindra.com/", "https://upload.wikimedia.org/wikipedia/commons/6/6e/Tech_Mahindra_New_Logo.svg", 20),
    Company("ltimindtree", "LTIMindtree", "mnc", "https://www.ltimindtree.com/", "https://www.ltimindtree.com/careers/", "https://upload.wikimedia.org/wikipedia/commons/1/10/LTIMindtree_Logo.svg", 20),
    Company("genpact", "Genpact", "mnc", "https://www.genpact.com/", "https://www.genpact.com/careers", "https://upload.wikimedia.org/wikipedia/commons/4/45/Genpact_logo.svg", 20),
    Company("amazon", "Amazon", "maang", "https://www.amazon.com/", "https://www.amazon.jobs/", "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg", 5),
    Company("microsoft", "Microsoft", "maang", "https://www.microsoft.com/", "https://careers.microsoft.com/", "https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg", 5),
    Company("google", "Google", "maang", "https://www.google.com/", "https://www.google.com/about/careers/", "https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg", 5),
    Company("apple", "Apple", "maang", "https://www.apple.com/", "https://jobs.apple.com/", "https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg", 5),
    Company("adobe", "Adobe", "mnc", "https://www.adobe.com/", "https://www.adobe.com/careers.html", "https://upload.wikimedia.org/wikipedia/commons/8/8d/Adobe_Corporate_Logo.svg", 10),
    Company("salesforce", "Salesforce", "mnc", "https://www.salesforce.com/", "https://careers.salesforce.com/", "https://upload.wikimedia.org/wikipedia/commons/f/f9/Salesforce.com_logo.svg", 10),
    Company("oracle", "Oracle", "mnc", "https://www.oracle.com/", "https://careers.oracle.com/", "https://upload.wikimedia.org/wikipedia/commons/5/50/Oracle_logo.svg", 10),
    Company("sap", "SAP", "mnc", "https://www.sap.com/", "https://www.sap.com/about/careers.html", "https://upload.wikimedia.org/wikipedia/commons/5/59/SAP_2011_logo.svg", 10),
    Company("nvidia", "NVIDIA", "mnc", "https://www.nvidia.com/", "https://www.nvidia.com/en-us/about-nvidia/careers/", "https://upload.wikimedia.org/wikipedia/commons/2/21/Nvidia_logo.svg", 10),
    Company("cisco", "Cisco", "mnc", "https://www.cisco.com/", "https://jobs.cisco.com/", "https://upload.wikimedia.org/wikipedia/commons/6/64/Cisco_logo.svg", 10),
)


def get_target_companies() -> list[Company]:
    return list(TARGET_COMPANIES)


def get_company_by_slug(slug: str) -> Company | None:
    normalized = slug.strip().lower()
    return next(
        (company for company in TARGET_COMPANIES if company.slug == normalized),
        None,
    )
