const { useState, useEffect } = React

const listing_limit = 300;

class Main extends React.Component {
	constructor(props) {
		super(props);
		this.state = {data: null, term:'', sort:'name', reverse: false};
		this.load.bind(this)();
		this._search = this.search.bind(this);
		this._reorder = this.reorder.bind(this);
	}

	load(){
		let xhr = new XMLHttpRequest();
		xhr.open('GET', 'https://gist.githubusercontent.com/Shadow-Bot/9b64e0f0452001883cb341fee975c12b/raw/data.json');
		xhr.onload = ()=>{
			if (xhr.status === 200) {
				let data = JSON.parse(xhr.responseText);
				if(data['@metadata']['compatible_since'] > 1.4){
					alert('Data format may be broken for this viewer!')
				}

				let minprice = 999999;
				data.point_packages.forEach((pp)=>{
					let np = Math.min(minprice, pp.approx_price_usd / pp.points);
					if(np < minprice) {
						minprice = np;
					}
				});
				data.store_items.forEach((i)=>{
					i['usd'] = Math.ceil((i.points*minprice * 100) / 100)
				});
				this.setState({data: data});
			} else {
				alert('Failed to look up store data: Error ' + xhr.status);
			}
		};
		xhr.send();
	}

	search(evt){
		this.setState({term: evt.target.value});
	}

	normalize(st){
		return st.replace(/-/g, ' ').toLowerCase()
	}

	reorder(order){
		let reverse = this.state.sort === order && !this.state.reverse;
		this.setState({sort: order, reverse: reverse});
	}

	render() {
		let eles=[];
		let minprice = 10000;
		let best_pack = "Unknown";
		let pack_price= -99;
		let listingCount = 0;
		if(this.state.data) {
			this.state.data.point_packages.forEach((pp)=>{
				let np = Math.min(minprice, pp.approx_price_usd / pp.points);
				if(np < minprice) {
					best_pack = pp.pack_name;
					minprice = np;
					pack_price = pp.approx_price_usd;
				}
			});

			let tmp = this.state.data.store_items.filter((it) => {
				if (it === '')
					return true;
				let t = this.normalize(this.state.term);
				return (
					this.normalize(it.categories.join(', ')).includes(t) ||
					this.normalize(it.name).includes(t) ||
					this.normalize(it.description).includes(t)
				);
			});

			listingCount = tmp.length;

			eles = tmp.sort((a, b)=>{
				let field = this.state.sort;
				let rev = this.state.reverse? -1:1;
				if (a[field] < b[field])
					return -1 * rev;
				if (a[field] > b[field])
					return rev;
				return 0;
			}).slice(0, listing_limit).map((it) => {
				return <DataRow key={it.name} data={it}/>
			});
		}

		return (
			<div>
				<h2>
					PoE MTX - Unofficial Store Item Browser
					[<span className={'gray inline'}>
						{this.state.data?'Last updated: '+timeStamp(new Date(this.state.data['@metadata']['timestamp']*1000)):'Loading...'}
					</span>]
				</h2>
				<div className={'searchbox'}>
					<label htmlFor={'searchbox'}>Search: </label>
					<input id='searchbox' type={'text'} onChange={this._search} value={this.state.term} autoFocus/>
				</div>
				<div className={'right'}>
					Estimated best Point Pack: <a href={'https://www.pathofexile.com/purchase'}>
						<i className={'pack_name'}>{best_pack}</i>
					</a><br />
					Approx Value: <i className={'pack_name'}>${pack_price} USD</i><br />
					<a href="https://github.com/shadowmoose/PoE-Store-Indexer" target={"_blank"}>View this project on Github.</a><br />
					<a href={'https://travis-ci.com/shadowmoose/PoE-Store-Indexer'} target={'_blank'}>
						<img src="https://travis-ci.com/shadowmoose/PoE-Store-Indexer.svg?branch=master" title={"View build page."}/>
					</a>
				</div>
				<div className={'disclaimer'}>
					Note: All prices, especially those in USD, are approximate. Some, or even all, of the data on this page may be incorrect.
					Please do all actual browsing and buying at <a href={'https://www.pathofexile.com/shop'}>https://www.pathofexile.com/shop</a>!
				</div>
				<table>
					<tbody>
					<tr>
						<th onClick={()=>{this._reorder('name')}}>Cosmetic</th>
						<th onClick={()=>{this._reorder('points')}}>Points</th>
						<th onClick={()=>{this._reorder('usd')}}>USD</th>
						<th onClick={()=>{this._reorder('description')}}>Description</th>
					</tr>
						{eles}
						{listingCount > listing_limit ? <tr><th>Remaining {listingCount - listing_limit} listings truncated...</th></tr> : null}
					</tbody>
				</table>
			</div>
		);
	}
}


function DataRow (props) {
	const data = props.data;
	const [visible, setVisible] = useState(false);
	const [imagePos, setImagePos] = useState({x: props.x, y: props.y});

	function showImage(evt) {
		setImagePos({
			x: evt.pageX,
			y: evt.pageY
		});
		setVisible(true)
	}

	return <tr key={data.name} onClick={showImage} onMouseLeave={()=>setVisible(false)}>
		<td><a href={data.link} onMouseEnter={showImage} target={'_blank'}>{data.name}</a></td>
		<td>{data.points}</td>
		<td>${data.usd}</td>
		<td>{data.description} {visible ? <DataImage key={data.name} src={data.image} alt={data.name} pos={imagePos}/> : null}</td>
	</tr>
}

function DataImage(props) {
	const src = props.src;
	const alt = props.alt;

	return <img src={src} alt={alt} style={{
		position: 'absolute',
		top: (props.pos.y) + 'px',
		left: props.pos.x + 'px',
		pointerEvents: 'none',
		transform: 'translate(0, -100%)'
	}}/>
}

ReactDOM.render(
	<Main />,
	document.getElementById('root')
);
