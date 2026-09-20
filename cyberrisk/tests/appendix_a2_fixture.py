"""Appendix A.2 of the paper, transcribed: the sentences of four FY2017 Item 1A cyber risk
discussions, whether the paper's algorithm captured each one, and the type it reported.

Entry: (captured, type_or_None, sentence).  "other" = "Text from other paragraphs".
"""
# (file, sentences the paper reports as captured: relevant paragraph + "other paragraphs")
FILINGS = {
    "apple":   ("0000320193_0000320193-17-000070_a10-k20179302017.htm", 19 + 4),
    "abbott":  ("0000001800_0001047469-18-000856_a2234264z10-k.htm", 8 + 0),
    "gm":      ("0001467858_0001467858-18-000022_gm201710k.htm", 18 + 2),
    "verizon": ("0000732712_0000732712-18-000009_a201710-k.htm", 13 + 0),
}
D, B, I, L, E = "Direct", "Indirect: Company Business", "Indirect: Internal Consequences", \
    "Indirect: Legal Consequences", "Indirect: Economic Consequences"

APPLE = [
 (True, D, "There may be losses or unauthorized access to or releases of confidential information, including personally identifiable information, that could subject the Company to significant reputational, financial, legal and operational consequences."),
 (True, B, "The Company's business requires it to use and store confidential information, including, among other things, personally identifiable information (\"PII\") with respect to the Company's customers and employees."),
 (True, B, "The Company devotes significant resources to network and data security, including through the use of encryption and other security measures intended to protect its systems and data."),
 (True, D, "But these measures cannot provide absolute security, and losses or unauthorized access to or releases of confidential information may still occur, which could materially adversely affect the Company's reputation, financial condition and operating results."),
 (True, B, "The Company's business also requires it to share confidential information with suppliers and other third parties."),
 (True, D, "Although the Company takes steps to secure confidential information that is provided to third parties, such measures may not be effective and losses or unauthorized access to or releases of confidential information may still occur, which could materially adversely affect the Company's reputation, financial condition and operating results."),
 (True, B, "For example, the Company may experience a security breach impacting the Company's information technology systems that compromises the confidentiality, integrity or availability of confidential information."),
 (True, L, "Such an incident could, among other things, impair the Company's ability to attract and retain customers for its products and services, impact the Company's stock price, materially damage supplier relationships, and expose the Company to litigation or government investigations, which could result in penalties, fines or judgments against the Company."),
 (True, D, "Although malicious attacks perpetrated to gain access to confidential information, including PII, affect many companies across various industries, the Company is at a relatively greater risk of being targeted because of its high profile and the value of the confidential information it creates, owns, manages, stores and processes."),
 (True, D, "The Company has implemented systems and processes intended to secure its information technology systems and prevent unauthorized access to or loss of sensitive data, including through the use of encryption and authentication technologies."),
 (True, D, "As with all companies, these security measures may not be sufficient for all eventualities and may be vulnerable to hacking, employee error, malfeasance, system error, faulty password management or other irregularities."),
 (True, B, "For example, third parties may attempt to fraudulently induce employees or customers into disclosing user names, passwords or other sensitive information, which may in turn be used to access the Company's information technology systems."),
 (True, B, "To help protect customers and the Company, the Company monitors its services and systems for unusual activity and may freeze accounts under suspicious circumstances, which, among other things, may result in the delay or loss of customer orders or impede customer access to the Company's products and services."),
 (True, B, "In addition to the risks relating to general confidential information described above, the Company may also be subject to specific obligations relating to health data and payment card data."),
 (True, B, "Health data may be subject to additional privacy, security and breach notification requirements, and the Company may be subject to audit by governmental authorities regarding the Company's compliance with these obligations."),
 (True, L, "If the Company fails to adequately comply with these rules and requirements, or if health data is handled in a manner not permitted by law or under the Company's agreements with healthcare institutions, the Company could be subject to litigation or government investigations, may be liable for associated investigatory expenses, and could also incur significant fees or fines."),
 (True, I, "Under payment card rules and obligations, if cardholder information is potentially compromised, the Company could be liable for associated investigatory expenses and could also incur significant fees or fines if the Company fails to follow payment card industry data security standards."),
 (True, E, "The Company could also experience a significant increase in payment card transaction costs or lose the ability to process payment cards if it fails to follow payment card industry data security standards, which would materially adversely affect the Company's reputation, financial condition and operating results."),
 (True, B, "While the Company maintains insurance coverage that is intended to address certain aspects of data security risks, such insurance coverage may be insufficient to cover all losses or all types of claims that may arise."),
]
APPLE_OTHER = [
 (True, D, "The Company may be subject to information technology system failures or network disruptions caused by natural disasters, accidents, power disruptions, telecommunications failures, acts of terrorism or war, computer viruses, physical or electronic break-ins, or other events or disruptions."),
 (True, B, "System redundancy and other continuity measures may be ineffective or inadequate, and the Company's business continuity and disaster recovery planning may not be sufficient for all eventualities."),
 (True, B, "Such failures or disruptions could adversely impact the Company's business by, among other things, preventing access to the Company's online services, interfering with customer transactions or impeding the manufacturing and shipping of the Company's products."),
 (True, E, "These events could materially adversely affect the Company's reputation, financial condition and operating results."),
]
ABBOTT = [
 (True, D, "Abbott depends on sophisticated information technology systems and a cyberattack or other breach of these systems could have a material adverse effect on Abbott's results of operations."),
 (True, D, "Similar to other large multi-national companies, the size and complexity of the information technology systems on which Abbott relies for both its infrastructure and products makes them susceptible to a cyberattack, malicious intrusion, breakdown, destruction, loss of data privacy, or other significant disruption."),
 (True, D, "These systems have been and are expected to continue to be the target of malware and other cyberattacks."),
 (True, D, "In addition, third party hacking attempts may cause Abbott's information technology systems and related products, protected data, or proprietary information to be compromised."),
 (True, D, "A significant attack or other disruption could result in adverse consequences, including increased costs and expenses, problems with product functionality, damage to customer relations, lost revenue, and legal or regulatory penalties."),
 (True, D, "Abbott invests in its systems and technology and in the protection of its products and data to reduce the risk of an attack or other significant disruption, and monitors its systems on an ongoing basis for any current or potential threats and for changes in technology and the regulatory environment."),
 (True, D, "There can be no assurance that these measures and efforts will prevent future attacks or other significant disruptions to any of the systems on which Abbott relies or that related product issues will not arise in the future."),
 (True, D, "Any significant attack or other disruption on Abbott's systems or products could have a material adverse effect on Abbott's business."),
]
GM = [
 (True, D, "Security breaches and other disruptions to information technology systems and networked products, including connected vehicles, owned or maintained by us, GM Financial, or third-party vendors or suppliers on our behalf, could interfere with our operations and could compromise the confidentiality of private customer data or our proprietary information."),
 (True, B, "We rely upon information technology systems and manufacture networked products, some of which are managed by third-parties, to process, transmit and store electronic information, and to manage or support a variety of our business processes, activities and products."),
 (True, B, "Additionally, we and GM Financial collect and store sensitive data, including intellectual property, proprietary business information, proprietary business information of our dealers and suppliers, as well as personally identifiable information of our customers and employees, in data centers and on information technology networks."),
 (True, B, "The secure operation of these systems and products, and the processing and maintenance of the information processed by these systems and products, is critical to our business operations and strategy."),
 (True, D, "Despite security measures and business continuity plans, these systems and products may be vulnerable to damage, disruptions or shutdowns caused by attacks by hackers, computer viruses, or breaches due to errors or malfeasance by employees, contractors and others who have access to these systems and products."),
 (True, I, "The occurrence of any of these events could compromise the operational integrity of these systems and products."),
 (True, B, "Similarly, such an occurrence could result in the compromise or loss of the information processed by these systems and products."),
 (True, I, "Such events could result in, among other things, the loss of proprietary data, interruptions or delays in our business operations and damage to our reputation."),
 (True, B, "In addition, such events could result in legal claims or proceedings, liability or regulatory penalties under laws protecting the privacy of personal information; disrupt operations; or reduce the competitive advantage we hope to derive from our investment in advanced technologies."),
 (False, None, "We have experienced such events in the past and, although past events were immaterial, future events may occur and may be material."),
 (True, B, "Portions of our information technology systems also may experience interruptions, delays or cessations of service or produce errors due to regular maintenance efforts, such as systems integration or migration work that takes place from time to time."),
 (True, I, "We may not be successful in implementing new systems and transitioning data, which could cause business disruptions and be more expensive, time-consuming, disruptive and resource intensive."),
 (True, I, "Such disruptions could adversely impact our ability to design, manufacture and sell products and services, and interrupt other business processes."),
 (True, D, "Security breaches and other disruptions of our in-vehicle systems could impact the safety of our customers and reduce confidence in GM and our products."),
 (True, B, "Our vehicles contain complex information technology systems."),
 (False, None, "These systems control various vehicle functions including engine, transmission, safety, steering, navigation, acceleration, braking, window and door lock functions."),
 (True, B, "We have designed, implemented and tested security measures intended to prevent unauthorized access to these systems."),
 (True, D, "However, hackers have reportedly attempted, and may attempt in the future, to gain unauthorized access to modify, alter and use such systems to gain control of, or to change, our vehicles' functionality, user interface and performance characteristics, or to gain access to data stored in or generated by the vehicle."),
 (True, D, "Any unauthorized access to or control of our vehicles or their systems or any loss of data could impact the safety of our customers or result in legal claims or proceedings, liability or regulatory penalties."),
 (True, D, "In addition, regardless of their veracity, reports of unauthorized access to our vehicles, their systems or data could negatively affect our brand and harm our business, prospects, financial condition and operating results."),
]
GM_OTHER = [
 (True, D, "We sometimes face attempts to gain unauthorized access to our information technology networks and systems for the purpose of improperly acquiring our trade secrets or confidential business information."),
 (True, B, "The theft or unauthorized use or publication of our trade secrets and other confidential business information as a result of such an incident could adversely affect our competitive position."),
]
VERIZON = [
 (True, D, "Cyberattacks impacting our networks or systems could have an adverse effect on our business."),
 (True, D, "Cyberattacks, including through the use of malware, computer viruses, dedicated denial of services attacks, credential harvesting and other means for obtaining unauthorized access to or disrupting the operation of our networks and systems and those of our suppliers, vendors and other service providers, could have an adverse effect on our business."),
 (True, D, "Cyberattacks may cause equipment failures, loss of information, including sensitive personal information of customers or employees or valuable technical and marketing information, as well as disruptions to our or our customers' operations."),
 (True, D, "Cyberattacks against companies, including Verizon, have increased in frequency, scope and potential harm in recent years."),
 (True, D, "Further, the perpetrators of cyberattacks are not restricted to particular groups or persons."),
 (False, None, "These attacks may be committed by company employees or external actors operating in any geography, including jurisdictions where law enforcement measures to address such attacks are unavailable or ineffective, and may even be launched by or at the behest of nation states."),
 (True, D, "Cyberattacks may occur alone or in conjunction with physical attacks, especially where disruption of service is an objective of the attacker."),
 (True, D, "While, to date, we have not been subject to cyberattacks which, individually or in the aggregate, have been material to our operations or financial condition, the preventive actions we take to reduce the risks associated with cyberattacks, including protection of our systems and networks, may be insufficient to repel or mitigate the effects of a major cyberattack in the future."),
 (True, D, "The inability to operate our networks and systems or those of our suppliers, vendors and other service providers as a result of cyberattacks, even for a limited period of time, may result in significant expenses to Verizon and/or a loss of market share to other communications providers."),
 (True, D, "The costs associated with a major cyberattack on Verizon could include expensive incentives offered to existing customers and business partners to retain their business, increased expenditures on cybersecurity measures and the use of alternate resources, lost revenues from business interruption and litigation."),
 (False, None, "The potential costs associated with these attacks could exceed the insurance coverage we maintain."),
 (True, D, "Further, certain of Verizon's businesses, such as those offering security solutions and infrastructure and cloud services to business customers, could be negatively affected if our ability to protect our own networks and systems is called into question as a result of a cyberattack."),
 (True, D, "Moreover, our increasing presence in the IoT industry with offerings of telematics products and services, including vehicle telematics, could also increase our exposure to potential costs and expenses and reputational harm in the event of cyberattacks impacting these products or services."),
 (True, B, "In addition, a compromise of security or a theft or other compromise of valuable information, such as financial data and sensitive or private personal information, could result in lawsuits and government claims, investigations or proceedings."),
 (True, E, "Any of these occurrences could damage our reputation, adversely impact customer and investor confidence, and could further result in a material adverse effect on Verizon's results of operation or financial condition."),
]
EXPECTED = {"apple": APPLE + APPLE_OTHER, "abbott": ABBOTT, "gm": GM + GM_OTHER, "verizon": VERIZON}
