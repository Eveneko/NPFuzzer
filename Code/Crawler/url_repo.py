github_list = (
    'https://github.com/HKUST-Aerial-Robotics/VINS-Fusion',
)


def get_url_list(github, gitlab):
    url_list = []
    if github:
        for url in github_list:
            url_list.append(url)
    if gitlab:
        pass
    return url_list

def std_table_name(repo_url):
    return repo_url.split('/')[-1]
     