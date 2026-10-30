// A small expression parser, never eval/Function. Only declared identifiers and indicators execute.
export function parseExpression(source) {
  const tokens=[]
  const regex=/\s*(?:(\d+(?:\.\d+)?)(?:pct)?|([A-Za-z_]\w*)|(>=|<=|==|!=|[+*/%().,[\]<>-]))/y
  let offset=0
  while(offset<source.trimEnd().length) {
    regex.lastIndex=offset;const match=regex.exec(source)
    if(!match) throw new Error(`Cú pháp chưa hỗ trợ: ${source.slice(offset)}`)
    tokens.push(match[1]!==undefined?{number:Number(match[1])}:match[2]||match[3]);offset=regex.lastIndex
  }
  if(tokens.length>250) throw new Error('Biểu thức quá dài.')
  let pos=0
  const peek=()=>tokens[pos]
  const consume=value=>{if(tokens[pos++]!==value) throw new Error(`Cú pháp không hợp lệ: cần ${value}`)}
  const levels={or:1,and:2,'>':3,'<':3,'>=':3,'<=':3,'==':3,'!=':3,crossover:3,crossunder:3,'+':4,'-':4,'*':5,'/':5,'%':5}
  function expression(min=0) {
    let left
    const token=tokens[pos++]
    if(token==='not'||token==='-') left={type:'unary',op:token,arg:expression(6)}
    else if(token==='(') { left=expression();consume(')') }
    else if(token&&typeof token==='object') left={type:'number',value:token.number}
    else if(typeof token==='string'&&/^[A-Za-z_]\w*$/.test(token)) {
      if(peek()==='(') {
        pos++;const args=[]
        if(peek()!==')') { args.push(expression()); while(peek()===',') { pos++; args.push(expression()) } }
        consume(')');left={type:'call',name:token,args}
      } else left={type:'ref',name:token}
    } else throw new Error('Biểu thức không hợp lệ.')
    while(peek()==='.'||peek()==='[') {
      if(peek()==='.') {pos++;const key=tokens[pos++];if(!['close','open','high','low','volume','is_long','upper','lower','middle'].includes(key)) throw new Error(`Thuộc tính chưa hỗ trợ: ${key}`);left={type:'property',arg:left,key}}
      else {pos++;const shift=tokens[pos++]?.number;if(!Number.isInteger(shift)||shift<0||shift>2000) throw new Error('Chỉ hỗ trợ truy cập lịch sử không âm.');consume(']');left={type:'history',arg:left,shift}}
    }
    while(typeof peek()==='string'&&levels[peek()]>=min) {
      const op=tokens[pos++];left={type:'binary',op,left,right:expression(levels[op]+1)}
    }
    return left
  }
  const tree=expression()
  if(pos!==tokens.length) throw new Error(`Cú pháp chưa hỗ trợ: ${String(peek())}`)
  return tree
}
export function applyBinary(op,a,b,previousA,previousB) {
  if(op==='and') return Boolean(a)&&Boolean(b)
  if(op==='or') return Boolean(a)||Boolean(b)
  if(op==='crossover'||op==='crossunder') {
    if(![a,b,previousA,previousB].every(Number.isFinite)) return false
    return op==='crossover'?a>b&&previousA<=previousB:a<b&&previousA>=previousB
  }
  if(![a,b].every(Number.isFinite)) return null
  switch(op) {
    case '+':return a+b
    case '-':return a-b
    case '*':return a*b
    case '/':return b===0?null:a/b
    case '%':return b===0?null:a%b
    case '>':return a>b
    case '<':return a<b
    case '>=':return a>=b
    case '<=':return a<=b
    case '==':return a===b
    case '!=':return a!==b
    default:throw new Error('Toán tử chưa hỗ trợ.')
  }
}
