using TheLegacy.Scryfall;

Console.WriteLine("=== TheLegacy ===");
Console.WriteLine("Unofficial Fan Content — not approved/endorsed by Wizards of the Coast.");
Console.WriteLine("Card data provided by Scryfall (https://scryfall.com).");
Console.WriteLine();

using var client = new ScryfallClient();
var provider = new BulkDataProvider(client);

var scryfallCards = await provider.GetOracleCardsAsync();
var cards = CardMapper.ToCards(scryfallCards);

Console.WriteLine();
Console.Write("Search for a card: ");
var query = Console.ReadLine()?.Trim();

if (!string.IsNullOrEmpty(query))
{
    var results = cards
        .Where(c => c.Name.Contains(query, StringComparison.OrdinalIgnoreCase))
        .Take(10)
        .ToList();

    if (results.Count == 0)
    {
        Console.WriteLine("No cards found.");
    }
    else
    {
        Console.WriteLine($"Found {results.Count} result(s):");
        Console.WriteLine();

        foreach (var card in results)
        {
            Console.WriteLine($"  {card.Name}  {card.ManaCost}");
            Console.WriteLine($"  {card.TypeLine}");
            if (!string.IsNullOrEmpty(card.OracleText))
                Console.WriteLine($"  {card.OracleText}");
            if (card.Power is not null && card.Toughness is not null)
                Console.WriteLine($"  {card.Power}/{card.Toughness}");
            Console.WriteLine();
        }
    }
}
