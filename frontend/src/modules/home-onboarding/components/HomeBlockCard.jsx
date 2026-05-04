export default function HomeBlockCard({ block }) {
  return (
    <article>
      <h3>{block.title}</h3>
      <p>{block.description}</p>
      {block.cta_label ? <span>{block.cta_label}</span> : null}
    </article>
  )
}
