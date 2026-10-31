# GAP-HOST 호스트 증거 수집 (읽기 전용)

- 수집 일시: 2026-10-31 13:02~13:03 KST, 호스트 `local`(DGX Spark, GB10)
- 수행자: OpenCode Qwen3.8-Flash-Next-IQ3_S (GAP-HOST 배정)
- 각 명령은 정확히 1회 실행. exit code는 실행 직후 captured 값. 발췌는 비밀·계정정보 없음.

## 1. GPU 스칼라 조회

```
$ nvidia-smi --query-gpu=name,driver_version,memory.used,memory.total,utilization.gpu,power.draw --format=csv
```
exit 0

```csv
name, driver_version, memory.used [MiB], memory.total [MiB], utilization.gpu [%], power.draw [W]
NVIDIA GB10, 595.58.03, [N/A], [N/A], 95 %, 42.50 W
```

→ 이름/드라이버/사용률/전력은 값, VRAM used/total은 `[N/A]`.

## 2. GPU 메모리 상세

```
$ nvidia-smi -q -d MEMORY | head -40
```
exit 0 (실제 출력 23줄, head 미달)

```
Driver Version                                         : 595.58.03
CUDA Version                                           : 13.2
Attached GPUs                                          : 1
GPU 0000000F:01:00.0
    FB Memory Usage
        Total                                          : N/A
        Reserved                                       : N/A
        Used                                           : N/A
        Free                                           : N/A
    BAR1 Memory Usage
        Total                                          : N/A
        Used                                           : N/A
        Free                                           : N/A
    Conf Compute Protected Memory Usage
        Total                                          : 0 MiB
        Used                                           : 0 MiB
        Free                                           : 0 MiB
```

→ FB/BAR1 메모리 전부 N/A. 0 MiB가 나오는 항목은 보호메모리뿐이며 이는 VRAM 사용량이 아니다.

## 3. GPU 프로세스별 메모리

```
$ nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
```
exit 0

```csv
pid, process_name, used_gpu_memory [MiB]
54922, /src/build/bin/llama-server, 72213 MiB
```

→ GPU 메모리성 수치는 프로세스 행으로만 관측됨 (llama-server 72,213 MiB).

## 4. 추론 서버 /metrics

```
$ curl -s -m3 localhost:8000/metrics | head -30
```
exit 0 (HTTP 본문은 에러 JSON)

```json
{"error":{"code":501,"message":"This server does not support metrics endpoint. Start it with `--metrics`","type":"not_supported_error"}}
```

→ 현재 llama-server는 metrics 엔드포인트 미지원(기동 플래그 부재). 재시작하지 않음.

## 5. 추론 서버 /props

```
$ curl -s -m3 localhost:8000/props | head -c 1500
```
exit 0 (발췌 앞부분)

```json
{"default_generation_settings":{"params":{"seed":4294967295,"temperature":1.0,...
"repeat_last_n":64,"repeat_penalty":1.0,...
```

→ 모델/서버 속성 JSON 응답 정상(생성 파라미터 기본값 등).

## 6. 추론 서버 /slots

```
$ curl -s -m3 localhost:8000/slots | head -c 800
```
exit 0 (발췌 앞부분)

```json
[{"id":0,"n_ctx":131072,"speculative":false,"is_processing":false,"id_task":1207,
"n_prompt_tokens":943,"n_prompt_tokens_processed":0,"n_prompt_tokens_cache":0,...
```

→ 슬롯 1개, n_ctx 131072, 처리 상태 관측 가능.

## 7. 사용자 linger

```
$ loginctl show-user $USER -p Linger
```
exit 0

```
Linger=no
```

## 8. 프로브 유닛 상태

```
$ systemctl --user is-enabled agent-observatory-probe.service
```
exit 0

```
enabled
```

→ 사용자 유닛 존재·enabled. (7)과 함께 보면 linger=no이므로 로그인 세션 밖 유지 보장은 안 됨.)

## 9. 실행 중 컨테이너 재시작 정책

```
$ docker inspect -f '{{.Name}} {{.HostConfig.RestartPolicy.Name}}' $(docker ps -q)
```
exit 0

```
/agent-observatory-app-1 unless-stopped
/agent-observatory-prometheus-1 unless-stopped
/agent-observatory-otel-collector-1 unless-stopped
/llm-server unless-stopped
```

## 10. docker 서비스 부팅 활성

```
$ systemctl is-enabled docker
```
exit 0

```
enabled
```

## 관찰 요약 (5줄)

1. GB10은 nvidia-smi로 이름·드라이버(595.58.03)·utilization(95%)·전력(42.5W)은 obtainable하지만 VRAM used/total은 query·상세 모두 N/A라 GPU 전용 메모리 수치는 생성 불가.
2. GPU 메모리 대체 관측점은 compute-apps뿐이며 llama-server 1개 프로세스가 72,213 MiB 점유로 관측된다.
3. 추론 서버(:8000)는 /props·/slots(JSON, n_ctx 131072 등) 정상 응답, /metrics는 501 미지원 — 기동 플래그(`--metrics`) 없이는 불가능하며 이번 점검에서 재시작하지 않았다.
4. `agent-observatory-probe.service` 사용자 유닛은 enabled이지만 `Linger=no` — 재부팅 후 비로그인 상태에서의 프로브 지속은 보장되지 않는다.
5. docker는 enabled이고 실행 중 4개 컨테이너(app·prometheus·otel-collector·llm-server) 전부 `unless-stopped` — 스택 자체는 부팅 시 자동 복귀 구성이며 게이지 수집 가능 여부는 위 1~4의 호스트 한도에 제약된다.
