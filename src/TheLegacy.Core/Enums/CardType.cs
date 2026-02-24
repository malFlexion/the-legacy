namespace TheLegacy.Core.Enums;

[Flags]
public enum CardType
{
    None = 0,
    Artifact = 1 << 0,
    Battle = 1 << 1,
    Creature = 1 << 2,
    Enchantment = 1 << 3,
    Instant = 1 << 4,
    Land = 1 << 5,
    Planeswalker = 1 << 6,
    Sorcery = 1 << 7,
    Kindred = 1 << 8,
}
