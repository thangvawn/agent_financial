export default function FinancialHealthScoreCard({ score, band, note }) {
  return (
    <article>
      <h2>Financial Health Score</h2>
      <p>{score}/100</p>
      <p>{band}</p>
      <p>{note}</p>
    </article>
  )
}
