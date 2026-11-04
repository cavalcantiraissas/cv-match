import { describe, expect, it } from "vitest";

import { faixaDoScore, formatarPercentual, formatarTamanho } from "./format";

describe("faixaDoScore", () => {
  it("segue os mesmos limites da classificação do backend", () => {
    expect(faixaDoScore(100)).toBe("good");
    expect(faixaDoScore(75)).toBe("good");
    expect(faixaDoScore(74)).toBe("warning");
    expect(faixaDoScore(60)).toBe("warning");
    expect(faixaDoScore(59)).toBe("serious");
    expect(faixaDoScore(40)).toBe("serious");
    expect(faixaDoScore(39)).toBe("critical");
    expect(faixaDoScore(0)).toBe("critical");
  });
});

describe("formatação", () => {
  it("formata percentuais em pt-BR", () => {
    expect(formatarPercentual(87.5, 1)).toBe("87,5%");
    expect(formatarPercentual(30)).toBe("30%");
  });

  it("formata tamanhos de arquivo", () => {
    expect(formatarTamanho(2048)).toBe("2 KB");
    expect(formatarTamanho(1.5 * 1024 * 1024)).toBe("1,5 MB");
  });
});
