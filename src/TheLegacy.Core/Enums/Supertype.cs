namespace TheLegacy.Core.Enums;

[Flags]
public enum Supertype
{
    None = 0,
    Basic = 1 << 0,
    Legendary = 1 << 1,
    Snow = 1 << 2,
    World = 1 << 3,
}
