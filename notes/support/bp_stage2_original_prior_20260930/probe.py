"""Paired stage-2 prior ablation with unchanged production BP stage 1."""
from pathlib import Path
import argparse
import hashlib
import inspect
import json
import numpy as np
from scipy.special import expit
from scipy.stats import binomtest
from color_code_stim import ColorCode
from color_code_stim.decoders.concat_matching_decoder import ConcatMatchingDecoder

OUT=Path(__file__).resolve().parent
ARCHIVE=OUT.parent/'bp_round2_audit_20260929'
BP=dict(bp_method='min_sum',max_iter=20,schedule='parallel')
METHODS=('current','stage2_only','selection_only','stage2_and_selection','ordinary_fallback')

def code(d,p):
    return ColorCode(d=d,rounds=2,p_depol=p,temp_bdry_type='Z',
        perfect_first_syndrome_extraction=True,exclude_non_essential_pauli_detectors=False,
        color_correlated_weight_basis='original_dem')

def write(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2)+'\n')

def mechanism_keys(manager):
    return [tuple(sorted(map(str,i.targets_copy()))) for i in manager.dem_xz if i.type=='error']

def stage1_keys(decomp,source_ids):
    h=decomp.Hs[0].tocsc();mapping=decomp.error_map_matrices[0].tocsr()
    return [(tuple(h.indices[h.indptr[j]:h.indptr[j+1]]),
             tuple(sorted(source_ids[mapping.indices[mapping.indptr[j]:mapping.indptr[j+1]]])))
            for j in range(h.shape[1])]

def stage2_sources(decomp,source_ids):
    mapping=decomp.error_map_matrices[1].tocsr()
    assert np.all(np.diff(mapping.indptr)==1)
    return source_ids[mapping.indices]

def run(name,d,p,det,actual):
    c=code(d,p);base=c.dem_manager;projection=base.global_projection
    base_decoder=ConcatMatchingDecoder(base,color_correlated_weight_basis='original_dem')
    ordinary=c.decode(det,check_validity=True)
    corr,llrs,conv=c.decode_bp(det,**BP);conv=np.asarray(conv,dtype=bool)
    bp_pred=np.asarray((corr.astype(np.uint8)@projection.observables.T)%2).ravel().astype(bool)
    np.testing.assert_array_equal(np.asarray((corr[conv].astype(np.uint8)@projection.H.T)%2,dtype=bool),det[conv])
    predictions={m:bp_pred.copy() for m in METHODS}
    predictions['ordinary_fallback'][~conv]=ordinary[~conv]
    base_keys=mechanism_keys(base);base_lookup={k:j for j,k in enumerate(base_keys)}
    assert len(base_keys)==len(base_lookup)
    physical_weight=np.log((1-base.probs_xz)/base.probs_xz)
    base1={};base2={}
    for color in 'rgb':
        decomp=base.dems_decomposed[color]
        keys=stage1_keys(decomp,np.arange(len(base_keys)))
        assert len(keys)==len(set(keys));base1[color]={k:j for j,k in enumerate(keys)}
        sources=stage2_sources(decomp,np.arange(len(base_keys)))
        assert len(sources)==len(set(sources));base2[color]={s:j for j,s in enumerate(sources)}
    checks=dict(fallback_shots=int((~conv).sum()),stage1_permutations=0,
                stage2_graph_permutations=0,independent_stage2_weight_checks=0,
                alternate_stage2_logical_differences=0)
    details=[]
    for counter,i in enumerate(np.flatnonzero(~conv)):
        local=base.with_dem(projection.project(expit(-llrs[i]),negative_log_weights=True))
        local_decoder=ConcatMatchingDecoder(local,color_correlated_weight_basis='original_dem')
        local_keys=mechanism_keys(local)
        assert set(local_keys)==set(base_keys)
        to_base=np.array([base_lookup[k] for k in local_keys])
        post_weight=np.empty(len(base_keys));post_weight[to_base]=np.log((1-local.probs_xz)/local.probs_xz)
        current=[];hybrid=[];alternate=[]
        for color in 'rgb':
            ld=local.dems_decomposed[color];bd=base.dems_decomposed[color]
            perm1=np.array([base1[color][k] for k in stage1_keys(ld,to_base)])
            assert len(set(perm1))==bd.Hs[0].shape[1]
            assert (ld.Hs[0]!=bd.Hs[0][:,perm1]).nnz==0
            # The BP-weighted first-stage solve is executed once and reused.
            first=local_decoder._decode_stage1(det[i:i+1],color)
            first_base=np.zeros_like(first);first_base[:,perm1]=first
            checks['stage1_permutations']+=1
            current_second,_=local_decoder._decode_stage2(det[i:i+1],first,color)
            current_local=ld.map_errors_to_org_dem(current_second,stage=2).astype(np.uint8)%2
            current_base=np.zeros_like(current_local);current_base[:,to_base]=current_local
            current.append(current_base[0])
            # Actual original-prior stage-2 graph, with translated virtual rows.
            second,weight=base_decoder._decode_stage2(det[i:i+1],first_base,color)
            hybrid.append((bd.map_errors_to_org_dem(second,stage=2).astype(np.uint8)%2)[0])
            # Independent implementation: keep posterior graph ordering, replace
            # only weights, and check its permutation equivalence/minimum cost.
            perm2=np.array([base2[color][s] for s in stage2_sources(ld,to_base)])
            rows=np.r_[np.arange(det.shape[1]),det.shape[1]+perm1]
            assert (ld.Hs[1]!=bd.Hs[1][rows,:][:,perm2]).nnz==0
            checks['stage2_graph_permutations']+=1
            custom={color:((ld.Hs[0],ld.probs[0]),(ld.Hs[1],bd.probs[1][perm2]))}
            alt,alt_weight=local_decoder._decode_stage2(det[i:i+1],first,color,custom)
            np.testing.assert_allclose(weight,alt_weight,rtol=1e-6,atol=1e-5)
            checks['independent_stage2_weight_checks']+=1
            alt_local=ld.map_errors_to_org_dem(alt,stage=2).astype(np.uint8)%2
            alt_base=np.zeros_like(alt_local);alt_base[:,to_base]=alt_local
            alternate.append(alt_base[0])
        current=np.array(current);hybrid=np.array(hybrid);alternate=np.array(alternate)
        for candidates in (current,hybrid,alternate):
            np.testing.assert_array_equal(np.asarray((candidates@base.H.T)%2,dtype=bool),np.broadcast_to(det[i],(3,det.shape[1])))
        current_obs=np.asarray((current@base.obs_matrix.T)%2).ravel().astype(bool)
        hybrid_obs=np.asarray((hybrid@base.obs_matrix.T)%2).ravel().astype(bool)
        alternate_obs=np.asarray((alternate@base.obs_matrix.T)%2).ravel().astype(bool)
        checks['alternate_stage2_logical_differences']+=int((hybrid_obs!=alternate_obs).sum())
        current_post=current@post_weight;current_phys=current@physical_weight
        hybrid_post=hybrid@post_weight;hybrid_phys=hybrid@physical_weight
        predictions['current'][i]=current_obs[np.argmin(current_post)]
        predictions['selection_only'][i]=current_obs[np.argmin(current_phys)]
        predictions['stage2_only'][i]=hybrid_obs[np.argmin(hybrid_post)]
        predictions['stage2_and_selection'][i]=hybrid_obs[np.argmin(hybrid_phys)]
        if predictions['current'][i]!=actual[i] or predictions['stage2_and_selection'][i]!=actual[i]:
            details.append(dict(index=int(i),actual=bool(actual[i]),
                current=bool(predictions['current'][i]),hybrid=bool(predictions['stage2_and_selection'][i]),
                current_candidates=current_obs.tolist(),hybrid_candidates=hybrid_obs.tolist(),
                current_posterior_scores=current_post.tolist(),hybrid_posterior_scores=hybrid_post.tolist(),
                current_physical_scores=current_phys.tolist(),hybrid_physical_scores=hybrid_phys.tolist()))
        if counter and counter%500==0:print(name,'fallback',counter,'/',checks['fallback_shots'],flush=True)
    # Validate the reconstructed baseline against the public production API.
    public,extra=c.decode(det,bp_predecoding=True,bp_prms=BP,metrics=['logical_error'],actual_observables=actual,check_validity=True)
    np.testing.assert_array_equal(public,predictions['current'])
    np.testing.assert_array_equal(extra['bp_converged'],conv)
    summary=dict(name=name,d=d,p=p,shots=len(det),bp_parameters=BP,checks=checks,
                 ordinary_failures=int((ordinary!=actual).sum()),converged=int(conv.sum()),
                 converged_failures=int(((bp_pred!=actual)&conv).sum()),methods={})
    reference=predictions['current']!=actual
    for method,pred in predictions.items():
        fail=pred!=actual;rescued=int((reference&~fail).sum());worsened=int((~reference&fail).sum())
        row=dict(failures=int(fail.sum()),fallback_failures=int((fail&~conv).sum()),
                 rescued=rescued,worsened=worsened,
                 rescued_vs_ordinary=int(((ordinary!=actual)&~fail).sum()),
                 worsened_vs_ordinary=int(((ordinary==actual)&fail).sum()),
                 paired_binomial_p=(None if name=='physical_d5' else
                     float(binomtest(rescued,rescued+worsened).pvalue) if rescued+worsened else 1.))
        if name=='physical_d5':row.update(single_failures=int(fail[:57].sum()),double_failures=int(fail[57:].sum()))
        summary['methods'][method]=row
    np.savez_compressed(OUT/f'{name}.npz',detectors=det,observables=actual,converged=conv,ordinary=ordinary,**predictions)
    write(f'{name}.json',summary);write(f'{name}_traces.json',details)
    print(json.dumps(summary),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('sample',choices=['physical_d5','paired_d5','paired_d7'])
    args=parser.parse_args()
    if args.sample=='physical_d5':
        z=np.load(ARCHIVE/'physical_inputs.npz');run(args.sample,5,.03,z['detectors'],z['observables'])
    elif args.sample=='paired_d5':
        z=np.load(ARCHIVE/'paired_inputs.npz');run(args.sample,5,.05,z['detectors'],z['observables'])
    else:
        c=code(7,.05);det,obs=c.sample(4096,seed=2026093007);run(args.sample,7,.05,det,obs)
    paths=[inspect.getfile(ColorCode),inspect.getfile(ConcatMatchingDecoder)]
    from color_code_stim.decoders.belief_concat_matching_decoder import BeliefConcatMatchingDecoder
    from color_code_stim.dem_utils.global_dem import GlobalDemProjection
    paths.extend([inspect.getfile(BeliefConcatMatchingDecoder),inspect.getfile(GlobalDemProjection)])
    write('provenance.json',dict(branch='codex/global-bp-predecoding-20260929',
        new_sample_seed=2026093007,new_sample_shots=4096,
        sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}))
