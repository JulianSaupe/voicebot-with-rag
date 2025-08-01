from backend.internal.adapters.driven.all_mpnet_base_v2 import AllMPNetBaseV2
from backend.internal.adapters.driven.postgres_db import PostgresVectorDB

if __name__ == '__main__':
    text = (
        "Ich bin Cora, sprich mit mir über die Ausstellung!"
        "Cora ist Teil eines Forschungsprojektes an der Universität Augsburg. Mit Hilfe von künstlicher"
        "Intelligenz ist sie in der Lage, Gespräche über Imitate, Fälschungen, Originale und natürlich"
        "das Museum Oberschönenfeld zu führen. Stell Cora deine Fragen!"
        "Mit freundlicher Unterstützung des Lehrstuhls für Menschzentrierte Künstliche Intelligenz der Universität"
        "Augsburg, namentlich Prof. Dr. Elisabeth André, Daksitha Withanage Don M.Sc. und Silvan Mertes M.Sc."
    )

    calculator = AllMPNetBaseV2()
    db = PostgresVectorDB(embedding_calculator=calculator)

    db.insert_document(text)
