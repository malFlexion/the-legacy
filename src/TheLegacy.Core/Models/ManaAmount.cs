namespace TheLegacy.Core.Models;

public class ManaAmount
{
    public int Generic { get; init; }
    public int White { get; init; }
    public int Blue { get; init; }
    public int Black { get; init; }
    public int Red { get; init; }
    public int Green { get; init; }

    public int ConvertedManaCost => Generic + White + Blue + Black + Red + Green;

    public override string ToString()
    {
        var parts = new List<string>();
        if (Generic > 0) parts.Add(Generic.ToString());
        if (White > 0) parts.Add(new string('W', White));
        if (Blue > 0) parts.Add(new string('U', Blue));
        if (Black > 0) parts.Add(new string('B', Black));
        if (Red > 0) parts.Add(new string('R', Red));
        if (Green > 0) parts.Add(new string('G', Green));
        return parts.Count > 0 ? string.Join("", parts) : "0";
    }

    public static ManaAmount Parse(string manaCost)
    {
        if (string.IsNullOrWhiteSpace(manaCost))
            return new ManaAmount();

        int generic = 0, white = 0, blue = 0, black = 0, red = 0, green = 0;

        // Scryfall format: {3}{W}{U} etc.
        var symbols = manaCost.Split(new[] { '{', '}' }, StringSplitOptions.RemoveEmptyEntries);

        foreach (var symbol in symbols)
        {
            if (int.TryParse(symbol, out var num))
                generic += num;
            else
            {
                foreach (var c in symbol)
                {
                    switch (c)
                    {
                        case 'W': white++; break;
                        case 'U': blue++; break;
                        case 'B': black++; break;
                        case 'R': red++; break;
                        case 'G': green++; break;
                    }
                }
            }
        }

        return new ManaAmount
        {
            Generic = generic,
            White = white,
            Blue = blue,
            Black = black,
            Red = red,
            Green = green,
        };
    }
}
