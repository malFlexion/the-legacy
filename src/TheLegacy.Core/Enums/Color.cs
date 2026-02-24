namespace TheLegacy.Core.Enums;

[Flags]
public enum Color
{
    Colorless = 0,
    White = 1 << 0,
    Blue = 1 << 1,
    Black = 1 << 2,
    Red = 1 << 3,
    Green = 1 << 4,
}
