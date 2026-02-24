using TheLegacy.Core.Models;

namespace TheLegacy.Core.Tests;

public class ManaAmountTests
{
    [Fact]
    public void Parse_StandardManaCost_ReturnsCorrectAmounts()
    {
        var mana = ManaAmount.Parse("{3}{W}{U}");

        Assert.Equal(3, mana.Generic);
        Assert.Equal(1, mana.White);
        Assert.Equal(1, mana.Blue);
        Assert.Equal(0, mana.Black);
        Assert.Equal(0, mana.Red);
        Assert.Equal(0, mana.Green);
        Assert.Equal(5, mana.ConvertedManaCost);
    }

    [Fact]
    public void Parse_EmptyString_ReturnsZero()
    {
        var mana = ManaAmount.Parse("");

        Assert.Equal(0, mana.ConvertedManaCost);
    }

    [Fact]
    public void Parse_SingleColor_ReturnsCorrectAmount()
    {
        var mana = ManaAmount.Parse("{R}");

        Assert.Equal(1, mana.Red);
        Assert.Equal(1, mana.ConvertedManaCost);
    }

    [Fact]
    public void ToString_ReturnsReadableFormat()
    {
        var mana = ManaAmount.Parse("{2}{B}{B}");

        Assert.Equal("2BB", mana.ToString());
    }
}
