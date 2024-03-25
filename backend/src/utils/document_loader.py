from llama_index.readers.web import TrafilaturaWebReader, RssReader, WholeSiteReader
from pyprojroot import here

urls = [
    "https://legalverse.io/",
    "https://legalverse.io/solution",
    "https://legalverse.io/features",
    "https://legalverse.io/careers",
    "https://legalverse.io/company",
    "https://legalverse.io/support",
    "https://legalverse.io/login",
    "https://legalverse.io/signup"]
# documents_whole_site = WholeSiteReader("").load_data([url])
# print(documents_whole_site)

documents_trafilatura = TrafilaturaWebReader().load_data(urls)
print(documents_trafilatura)

# for each Document, save it as a txt file
for document in documents_trafilatura:
    print(f"Saving {document.id_} to file")
    name = document.id_.replace("https://", "").replace(".io/", "_")
    with open(here(f"backend/src/utils/document_{name}.txt"), "w") as file:
        file.write(document.text)


