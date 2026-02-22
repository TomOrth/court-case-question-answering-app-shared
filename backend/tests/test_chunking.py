"""
Test chunking service.
"""

from app.services.chunking import chunk_document, count_words

def main():
    sample_text = """
UNITED STATES DISTRICT COURT
FOR THE DISTRICT OF IDAHO

MARTIN BELL, et al., Plaintiffs,
v.
CITY OF BOISE, Defendant.

Case No. 1:09-cv-00540-BLW

MEMORANDUM DECISION AND ORDER

This matter comes before the Court on Plaintiffs' Motion for Preliminary Injunction. 
The Court has reviewed the parties' briefs and supporting materials, and heard oral 
argument on the motion. For the reasons set forth below, the Court GRANTS the motion.

BACKGROUND

The City of Boise has enacted and enforces various ordinances that prohibit sleeping 
in public places. Plaintiffs are homeless individuals who have been cited under these 
ordinances. They contend that enforcement of these ordinances against homeless 
individuals who have no access to shelter violates the Eighth Amendment's prohibition 
on cruel and unusual punishment.

The plaintiffs in this case represent a class of homeless individuals who have been 
living on the streets of Boise. Many of them have been cited multiple times for 
violations of the camping and sleeping ordinances. The evidence shows that the 
shelters in Boise often reach capacity and turn away homeless individuals.

LEGAL STANDARD

To obtain a preliminary injunction, the moving party must establish: (1) likelihood 
of success on the merits; (2) likelihood of irreparable harm in the absence of 
preliminary relief; (3) that the balance of equities tips in the moving party's favor; 
and (4) that an injunction is in the public interest.

ANALYSIS

I. Likelihood of Success on the Merits

The Eighth Amendment prohibits the infliction of cruel and unusual punishment. This 
protection extends to punishment that is disproportionate to the offense or that 
punishes a person for their status rather than their conduct. In Robinson v. California, 
the Supreme Court held that criminalizing a person's status as a drug addict violated 
the Eighth Amendment.

The Court finds that enforcing the camping and sleeping ordinances against homeless 
individuals who have no access to shelter effectively criminalizes their status as 
homeless. When there is no available shelter space, a homeless person has no choice 
but to sleep outdoors. Punishing them for this involuntary conduct constitutes cruel 
and unusual punishment.

II. Irreparable Harm

Plaintiffs have demonstrated that they face irreparable harm absent injunctive relief. 
They continue to receive citations and face criminal penalties for conduct they cannot 
avoid. The ongoing threat of criminal prosecution causes significant harm that cannot 
be remedied through monetary damages.

III. Balance of Equities

The balance of equities favors the plaintiffs. While the City has a legitimate interest 
in maintaining public spaces, this interest does not outweigh the constitutional rights 
of homeless individuals. The City can pursue alternative approaches to address 
homelessness that do not criminalize the status of being homeless.

IV. Public Interest

An injunction serves the public interest by preventing the unconstitutional punishment 
of vulnerable individuals. The public has an interest in ensuring that constitutional 
protections are upheld, particularly for those who are least able to advocate for 
themselves.

CONCLUSION

For the foregoing reasons, Plaintiffs' Motion for Preliminary Injunction is GRANTED. 
The City of Boise is hereby ENJOINED from enforcing its camping and sleeping ordinances 
against homeless individuals on nights when there is no available shelter space.

IT IS SO ORDERED.

Dated: September 28, 2011

_____________________________
B. Lynn Winmill
Chief U.S. District Judge
    """

    print("Testing document chunking...")
    print(f"Document word count: {count_words(sample_text)}")
    print()

    chunks = chunk_document(
        document_id=78643,
        document_title="Memorandum Decision and Order",
        document_date="2011-09028",
        text=sample_text,
        target_chunk_size=200,
    )

    print(f"Created {len(chunks)} chunks:")
    print()

    for chunk in chunks:
        print(f"📃 {chunk.citation_id}")
        print(f"    Words: {chunk.word_count}")
        print(f"    Preview: {chunk.text}...")
        print()

    print("✅ Chunking wording correctly!")


if __name__ == "__main__":
    main()
