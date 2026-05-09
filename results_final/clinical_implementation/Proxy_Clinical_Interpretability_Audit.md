# Proxy Clinical Interpretability Audit

## Bottom Line

The proxy variables are clinically usable if they are explained as support-burden signals, not as direct drug-dose scores and not as full VIS. They are more abstract than vital signs or routine labs, so they require a short Methods/table definition before deployment.

## Required Questions

1. 它们是否过于抽象？ / Are they too abstract?

They are more abstract than bedside measurements, but not too abstract for an EHR-implemented prediction model if named as support-intensity burden proxies.

2. 临床医生是否容易理解？ / Are they easy for clinicians to understand?

`shared_support_intensity_proxy` is understandable as a total support-burden summary. Component variables require one-line clinical labels: hemodynamic support burden, lactate/perfusion burden, renal support burden, and respiratory support burden.

3. 是否需要解释为“支持强度负荷”而不是“药物剂量评分”？

Yes. They should be described as cross-database support-intensity burden signals. They are not full VIS and should not be presented as vasoactive dose scores.

4. `shared_support_intensity_proxy` 是否可作为最简解释方案？

Yes. It is suitable as the simplest clinical explanation and is the P10 proxy choice.

5. `shared_support_intensity_proxy + support_lactate_component` 是否适合作为兼顾解释性的双指标方案？

Yes. This is the best communication compromise: the shared proxy gives total support burden, while the lactate component gives a perfusion/low-flow explanation that clinicians recognize.

6. 是否存在与 full VIS 混称风险？

Yes, if wording is loose. The mitigation is to always use `shared support-intensity proxy` and avoid any wording that equates the proxy with VIS, eICU-derived VIS, or a drug-dose score.

7. 如何用一句中文解释这些 proxy？ / One-sentence Chinese explanation

这些 proxy 变量表示患者在循环、灌注、肾脏和呼吸方面接受或需要支持的总体负荷，用于跨数据库稳定表达病情支持强度，并不是 full VIS 或单纯药物剂量评分。

## Feature-Level Proxy Notes

- `shared_support_intensity_proxy`: total cross-database support-burden summary; suitable for P10.
- `support_hemodynamic_component`: circulatory support burden; useful in full P15 explanation.
- `support_lactate_component`: perfusion/lactate burden; suitable for P12 dual-index explanation.
- `support_renal_component`: renal support/decline burden; useful in full P15 explanation.
- `support_respiratory_component`: respiratory support escalation burden; useful in full P15 explanation.
